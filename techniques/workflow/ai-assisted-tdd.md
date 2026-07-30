---
id: ai-assisted-tdd
title: Test-Driven Development with AI agents
category: workflow
ecosystems: [claude-code, claude-sdk, claude-api, generic]
problem: AI agents skip tests or write tests that don't capture requirements, leading to false-passing code
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [plan-then-execute, checkpoint-commit-discipline, iterative-self-refinement]
supersedes: []
sources:
  - {url: "https://code.visualstudio.com/docs/agents/guides/test-driven-development-guide", kind: docs, date: "2026-07-28"}
  - {url: "https://medium.com/@giorgio.zoppi/test-driven-development-with-agentic-ai-cdc8b494542d", kind: blog, date: "2026-07-28"}
  - {url: "https://elite-ai-assisted-coding.dev/p/guide-ai-agents-through-test-driven-development", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Agents can write plausible-looking code that passes a weak test suite but fails in production. Without tests written first, the agent has no clear spec to code against. Also, agents tend to peek at existing code while writing tests, reducing their value as specification—they write tests that match the current implementation, not the ideal behavior.

## How it works

Enforce the classic Red-Green-Refactor loop:

1. **Red:** Write tests based only on requirements, not implementation. Tests should fail because the feature doesn't exist yet.
2. **Green:** Implement the minimal code to pass all tests.
3. **Refactor:** Improve code quality while keeping tests green.

For agents, the key is running each phase in isolation: the test-writing agent cannot see the implementation code (or only its spec), and the implementation agent is then told "Do not stop until all tests pass."

## Setup

1. **Isolate test generation:** Run the test-writing phase from a context that excludes implementation code. If using Claude Code, launch from `/tests` directory only, not the app root. Provide only the spec/requirements and the interfaces the tests should target.

   ```bash
   # Launch agent from test directory only
   cd /project/tests
   # Agent cannot access /project/src implementation
   ```

2. **Write tests to spec:** Provide the agent with clear requirements and function signatures. Example: "Write tests for a `jwt.verify(token: str) -> dict` function. Requirements: must validate signature, must check expiration, must raise ValueError if invalid."

3. **Human review tests:** Before implementation, review tests to ensure they truly capture behavior, not just existing code. Adjust as needed.

4. **Implement iteratively:** Direct the implementation agent: "Make all tests pass. Do not return until the test suite is 100% green."

5. **Automate test runs:** After each change, run tests automatically. Agents improve rapidly when they get immediate feedback.

## When to use / when NOT

**Use when:**
- Feature has clear, nameable inputs/outputs
- Logic is pure or has deterministic side effects
- You can write good tests (and the agent is just automating what you'd write)
- Correctness is critical

**Skip when:**
- UI-heavy features (tests are fragile, hard to specify)
- Highly exploratory work (requirements unclear)
- True one-off scripts

## Tradeoffs

**Wins:** Clear spec, agent has no ambiguity, tests catch bugs before you see them, refactoring is safe.

**Costs:** Writing good tests is work; agents sometimes generate tests that are too permissive; test coverage gaps still exist (agent won't test what you didn't spec).

## Example

```
Phase 1 — Write Tests (agent working from /tests only):

test_jwt.py:
  def test_valid_signature():
    token = create_valid_token()
    result = jwt.verify(token)
    assert result['sub'] == 'user123'
  
  def test_expired_token():
    token = create_expired_token()
    with pytest.raises(ValueError, match="expired"):
      jwt.verify(token)
  
  def test_invalid_signature():
    token = "eyJhbGc.eyJzdWI.INVALID"
    with pytest.raises(ValueError, match="signature"):
      jwt.verify(token)

Phase 2 — Implement (agent working from /src):

Agent: "Running tests..."
  → 3 tests, 3 failures (functions don't exist)
Agent: "Writing jwt.py..."
Agent: "Re-running tests..."
  → 1 pass, 2 fail (missing validation)
Agent: "Adding expiration check..."
Agent: "Re-running tests..."
  → All 3 pass ✓
```

## Notes & links

- Research caution: Telling agents to "do TDD" can actually increase regressions if they're not also given explicit test lists to check. Better to say "make these specific tests pass."
- Advanced pattern: test-driven agent prompting itself (TestDAD) — treat agent prompts as specs, write tests for agent behavior, iteratively refine prompts until tests pass
- Integration with CI/CD: automated test runs after every agent commit make the feedback loop tight
