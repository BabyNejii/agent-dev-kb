---
id: mutation-testing-agent-code
title: Mutation testing to verify AI-generated test quality
category: eval
ecosystems: [claude-code, claude-sdk]
problem: AI-generated tests reach high coverage but have weak assertions; mutations expose gaps
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: []
supersedes: []
sources:
  - {url: "https://www.augmentcode.com/guides/mutation-testing-ai-generated-code", kind: blog, date: "2026-03-10"}
  - {url: "https://www.thoughtworks.com/radar/techniques/mutation-testing", kind: blog, date: "2025-10-15"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

AI-generated tests often achieve 80%+ line coverage but rely on weak assertions: checking non-null instead of verifying actual values, mocking rather than validating behavior. Traditional coverage metrics don't expose these gaps. You need a way to confirm tests actually verify code behavior, not just execute it.

## How it works

Mutation testing injects deliberate faults (mutations) into source code and checks whether the test suite detects them. A mutation that the tests fail to catch (a "survivor") reveals an assertion gap that the AI overlooked.

**The feedback loop for agent workflows:**
1. Agent writes code and generates tests
2. Mutation tool runs on the code, creating 50–1000 variants (each with one bug)
3. Test suite runs against each mutant; classify as killed (tests caught it), survived (tests missed it), or equivalent (mutation doesn't change behavior)
4. Feed surviving mutants back to the agent: "Your tests missed this mutation: [mutant code]. Write a test that catches it."
5. Agent re-runs mutations to confirm fix

## Setup

1. **Choose tool by language:**
   - **Python:** `mutmut` (lightweight, easy integration)
   - **JavaScript/TypeScript:** `stryker` (comprehensive, good CI integration)
   - **Java:** `pit` (mature, widely used)
   - **C#:** `stryker.net`

2. **Run mutations on changed code only (cost control):**
```python
# mutmut example—scope to diff
mutmut run --paths-to-mutate src/ --tests-dir tests/ \
  --mutation-operators=all \
  --max-workers=8 \
  --incremental  # Reuse prior results
```

3. **Classify survivors and feed back to agent:**
```python
survivors = parse_mutation_report("mutmut-report.json")
for s in survivors:
    if not is_equivalent(s):  # Real bug, not equivalent mutation
        agent_prompt = f"""
        Your test suite missed this mutation:
        {s.code_with_mutation}
        
        Write a test that catches it.
        """
        new_test = agent.write_test(agent_prompt)
        verify_kills_mutation(new_test, s)
```

4. **Set gates by criticality:**
```python
# thresholds: if X% of mutations are killed
KILL_THRESHOLDS = {
    "payment": 0.85,      # 85% kill rate
    "auth": 0.85,
    "core": 0.70,
    "feature": 0.50,
}
if kill_rate < KILL_THRESHOLDS[code_type]:
    fail_ci()
```

## When to use / when NOT

**Use when:**
- AI is generating tests (especially for critical paths)
- You need proof that tests verify behavior, not just coverage
- Testing payment, auth, or security-sensitive code
- You can afford 5–30s per test file (mutation is slow)

**NOT when:**
- Testing UI or integration tests (mutations rarely meaningful)
- Budget is extremely tight (mutation testing runs dozens of variants)
- Line coverage is adequate and code is low-risk

## Tradeoffs

**Pros:**
- Exposes weak assertions that coverage metrics hide
- Provides concrete feedback (survivors) for the agent to fix
- Mutation kill rate is a more trustworthy signal than % coverage

**Cons:**
- Expensive: 5–30x slower than running tests once
- Many equivalent mutations require manual filtering
- Thresholds vary by domain; no universal "good" score

## Example

**AI writes code and test:**
```python
def parse_amount(s: str) -> float:
    return float(s)  # Bug: doesn't handle "$100.50"

def test_parse_amount():
    assert parse_amount("50.5") is not None  # Weak assertion
```

**Mutations generated:**
- `return 0.0` instead of `float(s)` → test passes (doesn't check value)
- `return float(s) + 1` → test passes (doesn't check magnitude)
- Add `if not s: return 0` → test passes (no edge case test)

**Mutation report:** 0/3 killed = 0% kill rate → FAIL

**Feedback to agent:**
```
Your test didn't catch:
  return float(s) + 1

Rewrite your test to catch this mutation.
```

**AI improves:**
```python
def test_parse_amount():
    assert parse_amount("50.5") == 50.5  # Now catches mutation
    assert parse_amount("$100.50") == 100.50  # Catches format bug
```

New mutation report: 3/3 killed = 100% kill rate → PASS

## Notes & links

- **Incremental runs:** Reuse prior results (`--incremental`) to save time on diffs
- **Scope to changed code:** Run full mutation on nightly; PR gate on changed files only
- **Caution:** Do not let the agent see the tests while writing mutations—it will write mutations to pass the tests, not to find real bugs
- **Complementary:** Combine with [[adversarial-code-review]] for defense in depth
