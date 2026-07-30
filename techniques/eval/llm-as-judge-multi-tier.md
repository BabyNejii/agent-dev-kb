---
id: llm-as-judge-multi-tier
title: Tiered LLM-as-judge architecture for cost-efficient code evaluation
category: eval
ecosystems: [claude-code, claude-sdk, claude-api]
problem: Single-model judges are expensive at scale; need cost-effective frontline filtering
maturity: established
confidence: reported
effort_to_adopt: medium
works_with: [adversarial-code-review]
supersedes: []
sources:
  - {url: "https://zylos.ai/research/2026-04-10-llm-as-judge-production-agent-verification-2026/", kind: blog, date: "2026-04-10"}
  - {url: "https://galileo.ai/blog/why-llm-as-a-judge-fails", kind: blog, date: "2026-07-28"}
  - {url: "https://arxiv.org/pdf/2512.20159", kind: paper, date: "2025-12-20"}
added: "2026-07-28"
updated: "2026-07-30"
---

## Problem

Running a frontier LLM judge (Claude, GPT-4) on every agent output is prohibitively expensive at scale. You need a filter that catches obvious errors cheaply, reserving expensive judges for nuanced decisions.

## How it works

Deploy judges in a three-tier hierarchy by cost and depth:

1. **Deterministic checks** (near-zero cost, 100% coverage): Schema validation, JSON parsing, tool-call format, length bounds, safety filters. These catch 40–60% of hallucinations mechanistically.

2. **Small distilled judge** (milliseconds, high throughput): 3B–8B parameter models (Prometheus 2, Galileo Luna, Patronus Lynx) run on hallucination detection, factuality grounding, and basic correctness. Costs ~1–5% of frontier judge.

3. **Frontier judge** (higher latency/cost, selective use): Full Claude or similar for nuanced semantic scoring, reasoning quality, and complex task correctness on high-stakes or ambiguous cases only.

## Setup

1. Build deterministic checks first:
```python
def validate_tool_call(call):
    """Deterministic checks that cost nothing."""
    if call["tool"] not in available_tools:
        return False, f"Unknown tool: {call['tool']}"
    schema = tool_schemas[call["tool"]]
    if not all(required in call["args"] for required in schema["required"]):
        return False, "Missing required arguments"
    return True, None
```

2. Set up small judge as a gated pass:
```python
# Only send to small judge if deterministic checks pass
if deterministic_valid:
    small_judge_verdict = call_distilled_judge(code, criteria)
    if small_judge_verdict["confidence"] < 0.6:
        # Escalate to frontier judge
        return call_frontier_judge(code, spec)
```

3. Track which tier caught issues (for ROI accounting):
```python
metrics = {
    "caught_by_deterministic": 0,
    "caught_by_small_judge": 0,
    "caught_by_frontier": 0,
}
```

## When to use / when NOT

**Use when:**
- Running continuous evaluation on high-volume agent output
- Cost per evaluation matters more than absolute accuracy
- You have budget constraints but need confidence gates
- Building production agent loops with runtimes < 2s

**NOT when:**
- Evaluating a one-time high-stakes deliverable (use frontier judge directly)
- You need >95% recall on subtle semantic errors (small judges plateau ~90%)
- Domain is highly specialized (distilled judges lose domain specificity)

## Tradeoffs

**Pros:**
- 97% cost reduction vs. all-frontier-judge (reported in Zylos 2026)
- Deterministic layer is fast enough for real-time gates
- Easy to audit and debug (each tier has clear contracts)

**Cons:**
- Misses some semantic bugs that frontier judge would catch
- Requires tuning thresholds for your domain (small judges aren't universal)
- Small judge model families sometimes have correlated blind spots

## Example

Production stack at a large AI-native software co (2026):
```python
# Tier 1: Free checks
assert_no_unknown_tools(code)
assert_valid_json(output)
assert_length_within_bounds(output)

# Tier 2: Cheap judge (runs on 100% of outputs)
if deterministic_pass:
    small = judge_7b(code, rubric="hallucinated_api,syntax,imports")
    if small.confidence > 0.75:
        return small.verdict  # PASS or list of issues
    
# Tier 3: Full judge (10% of outputs)
if small.confidence < 0.75 or small.verdict == "FAIL":
    full = judge_claude(code, spec, reasoning=True)
    return full.verdict
```

Result: 87% of checks resolved at tier 1/2, 13% escalated to Claude. Mean latency 150ms (deterministic + tier-2), cost per eval ~$0.001 (vs. $0.04 for all-Claude).

## Notes & links

- Zylos 2026 recommends starting with open-weight Prometheus-2-7b for tier 2; it scores well on code hallucination and imports-exist checks.
- Most production teams now use this pattern; all-frontier-judge is reserved for acceptance gates.
- Bias in LLM judges is detectable and fixable—run the same pair twice with swapped order; if verdict flips, you have order bias. Mitigation: randomize presentation order or use structured rubrics.
