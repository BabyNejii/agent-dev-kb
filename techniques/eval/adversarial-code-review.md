---
id: adversarial-code-review
title: Adversarial code review with fresh-context verifier agents
category: eval
ecosystems: [claude-code, claude-sdk, claude-api, antigravity]
problem: Agents cannot reliably review their own code; same-context verification misses bugs
maturity: established
confidence: reported
effort_to_adopt: medium
works_with: [llm-as-judge-multi-tier]
supersedes: []
sources:
  - {url: "https://www.augmentcode.com/guides/adversarial-code-review", kind: blog, date: "2026-03-15"}
  - {url: "https://arxiv.org/pdf/2604.16399", kind: paper, date: "2026-04-16"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

When an agent writes code and then reviews it in the same context, it rarely finds its own bugs. The agent has already committed to the reasoning that produced the code and lacks the independence to second-guess itself. This extends to testing: an agent that controls both test generation and verification often weakens tests to pass rather than strengthen assertions.

## How it works

**The maker-checker pattern:** A builder agent writes code in full context (task spec, reasoning, tool access). A fresh verifier agent receives only the diff and evaluation criteria, with no knowledge of the builder's reasoning. The verifier has read-only tools and a skeptical mindset. Crucially, the verifier is isolated in a separate agent/context window, often using a different model family to avoid correlated blind spots.

The structural isolation forces genuine independence: the verifier cannot rationalize the builder's mistakes because it never sees the reasoning that produced them.

## Setup

1. **Separate builder and verifier into different agents/conversations:**
```python
# Builder: full context, implementation focus
builder_response = claude(
    system="You are writing production code for: [SPEC]",
    context=[spec, requirements, conversation_history],
    tools=[read, write, test, execute],
)

# Verifier: fresh context, read-only, adversarial
verifier_response = claude(
    system="You are a skeptical code reviewer. Find issues.",
    context=[spec, builder_diff_only],  # NOT builder reasoning
    tools=[read, grep],  # Read-only only
    model="claude-3-5-sonnet",  # Different model family optional
)
```

2. **Verifier checklist (structured output):**
```python
verifier_prompt = """
Review this diff against the spec. Output JSON:
{
  "verdict": "PASS" | "FAIL",
  "issues": [
    {"severity": "critical|high|medium|low", "finding": "..."}
  ],
  "confidence": 0.0-1.0
}
"""
```

3. **Wire into CI/CD as a blocking gate:**
```python
# GitHub Actions example
- name: Adversarial Review
  run: |
    gh api repos/$REPO/issues/$PR \
      -f model=claude-3-5-sonnet \
      -f verifier_only=true \
      > review.json
    if grep -q '"verdict": "FAIL"' review.json; then
      exit 1  # Block merge
    fi
```

## When to use / when NOT

**Use when:**
- Building production agent loops that write code unsupervised
- Permission changes, authentication, or security-sensitive code
- Large diffs (>500 lines) from a single agent
- You can tolerate 5–10s latency before gating a merge

**NOT when:**
- Evaluating small tweaks or formatting changes (overhead > value)
- Prototype/sandbox code with no production impact
- Budget is extremely tight (verifier adds ~2x cost)

## Tradeoffs

**Pros:**
- Catches bugs self-review misses (especially off-by-one, null checks, edge cases)
- Prevents self-confirmation bias and spec drift
- One team reported finding 30–50% more issues with fresh-context review

**Cons:**
- Doubles latency and cost of code review
- Requires careful prompt tuning (verifier prompts are brittle)
- Different model families can have different blind spots (no universal fix)

## Example

**Builder writes code:**
```python
def process_batch(items):
    results = []
    for i in range(len(items)):
        results.append(transform(items[i]))
    return results
```

**Builder's self-review (same context):** "Looks good, clean loop."

**Fresh-context verifier review:**
- Missing null check: what if `items[i]` is None?
- No error handling: what if `transform()` raises?
- Off-by-one risk: loop index `i` starts at 0, correct? (Actually correct, but verifier flags it as worth double-checking.)

**Result:** Builder adds validation; merges only after verifier re-approves.

## Notes & links

- Start with advisory mode (findings posted but not blocking) to calibrate trust before gating.
- Verifier should be a different model family if budget allows—Codex reviewers caught bugs Claude-family review missed (resulting in published CVEs).
- Key constraint: verifier must NOT see the builder's reasoning or the full conversation. Paste only the diff + spec.
- Related: [[llm-as-judge-multi-tier]] to reduce cost; [[mutation-testing-agent-code]] to complement review with mechanical verification.
