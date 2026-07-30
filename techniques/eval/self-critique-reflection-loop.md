---
id: self-critique-reflection-loop
title: Self-critique reflection loops for agent code generation
category: eval
ecosystems: [claude-code, claude-sdk, claude-api]
problem: First-draft agent output often has fixable errors; iteration improves quality
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [llm-as-judge-multi-tier]
supersedes: []
sources:
  - {url: "https://www.taskade.com/blog/self-improving-ai-agents-reflection", kind: blog, date: "2026-02-10"}
  - {url: "https://medium.com/@swapnilshekade/reflective-and-self-improving-agents-building-ai-systems-that-critique-iterate-and-learn-from-fd3a57f62085", kind: blog, date: "2026-03-15"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

AI agents often generate code, scripts, or plans that work on the happy path but miss edge cases, error handling, or performance concerns. A single pass accepts the first output; structured reflection before returning catches fixable errors and improves success rates by 25–50%.

## How it works

**The reflection loop:** Generate → Critique → Revise → Check quality → Repeat (if not met) or Return.

The agent produces an answer, then pauses to evaluate it against concrete criteria (tests pass? spec met? edge cases handled?), identifies gaps, revises, and repeats. Crucially, the critic is grounded in objective signals (test results, linting, spec requirements) rather than the agent's own opinion.

**Key insight:** Separation of concerns. Producing code and judging code are different tasks. By splitting them, the agent can catch mistakes it would rationalize away in a single pass.

## Setup

1. **Basic reflection loop (2–3 iterations):**
```python
def generate_with_reflection(spec: str, max_iterations: int = 3):
    code = agent.generate(spec)
    
    for iteration in range(max_iterations):
        # Critique against objective criteria
        is_valid, errors = validate(code)
        tests_pass = run_tests(code)
        
        if is_valid and tests_pass:
            return code  # Success
        
        # Revise based on feedback
        feedback = f"Tests: {tests_pass}. Errors: {errors}"
        code = agent.revise(f"Fix the following issues:\n{feedback}")
    
    return code  # Return after max iterations
```

2. **Grounding the critique (critical):**
```python
def critique_code(code: str) -> dict:
    """Judge code against objective signals, not opinion."""
    return {
        "tests_pass": run_pytest(code),
        "lint_clean": run_flake8(code),
        "type_errors": run_mypy(code),
        "coverage": measure_coverage(code),
        "spec_met": check_spec_compliance(code, spec),
    }
```

3. **Avoid self-confirmation bias by using external judges:**
```python
# WRONG: Agent critiques its own code
critique = agent.generate("Review this code: [code]")

# RIGHT: Grounded critique
critique = {
    "tests_pass": run_tests(code) == 0,
    "spec_met": spec_validator.check(code),
}
```

4. **Multi-agent debate (optional, higher cost):**
```python
# Use different critic personas to catch correlated blind spots
critiques = [
    agent_base.critique(code),      # Default
    agent_strict.critique(code),    # Strict/skeptical
    agent_creative.critique(code),  # Creative/adversarial
]

issues = merge_critiques(critiques)  # Union or consensus
```

## When to use / when NOT

**Use when:**
- Generating code that must be correct (tests are expensive to fix later)
- Task is multi-step (planning, implementation, validation)
- Agent often ships nearly-correct output that's close to passing
- Time to quality matters more than latency

**NOT when:**
- One-pass correctness is rare (many errors too deep to fix by iteration)
- Latency is critical (reflection adds 2–10s per call)
- Output validation is expensive (each iteration runs the test suite)

## Tradeoffs

**Pros:**
- 25–50% improvement in success rates (reported)
- Catches fixable errors before shipment
- Low complexity; works with existing agent setups
- Very effective for code generation (errors are testable)

**Cons:**
- Doubles latency (2–3 iterations of generation + testing)
- Over-iteration can degrade quality (diminishing returns after 3 rounds)
- Agent can get stuck reinforcing same flawed reasoning without external signal

## Example

**Without reflection:**
```python
def fibonacci(n):
    if n <= 1: return n
    return fibonacci(n-1) + fibonacci(n-2)  # Inefficient but works
```

Test: `fibonacci(40)` times out. Fails.

**With reflection:**

Iteration 1:
- Generate code (above)
- Run tests → Timeout on n=40
- Feedback: "Timeout detected. Use memoization or iterative approach."

Iteration 2:
- Revise:
```python
def fibonacci(n, memo={}):
    if n in memo: return memo[n]
    if n <= 1: return n
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]
```
- Run tests → Pass

Return memoized version.

**Result:** One extra iteration caught exponential performance bug.

## Notes & links

- Cap iterations at 3–5; most teams see diminishing returns after round 2.
- Ground the critic in tests and linters, NOT in the agent's opinion.
- If the agent says "looks good," that's not a signal. If tests pass, that is.
- Degeneration of thought is a real risk: if the agent keeps reinforcing the same mistake, iteration makes it worse. Detect this by checking if revision changes the code; if not, stop.
- Multi-agent debate is 2–5x more expensive; use sparingly for high-stakes code.
- Related: [[llm-as-judge-multi-tier]] to make the critique layer cheaper.
