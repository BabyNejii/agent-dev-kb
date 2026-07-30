---
id: plan-then-execute
title: Plan-then-Execute pattern for structured agent workflows
category: workflow
ecosystems: [claude-code, claude-sdk, claude-api, generic]
problem: Agents executing without a plan produce meandering, error-prone changes and waste compute
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [ai-assisted-tdd, human-in-loop-review, checkpoint-commit-discipline]
supersedes: []
sources:
  - {url: "https://dev.to/varun_pratapbhardwaj_b13/separation-of-planning-and-execution-the-key-pattern-for-reliable-ai-coding-agents-5b53", kind: blog, date: "2026-07-28"}
  - {url: "https://community.sap.com/t5/security-and-compliance-blog-posts/plan-then-execute-an-architectural-pattern-for-responsible-agentic-ai/ba-p/14239753", kind: blog, date: "2026-07-28"}
  - {url: "https://agentpatterns.ai/workflows/research-plan-implement/", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Agents that move directly from problem statement to implementation often make hidden architectural mistakes, miss edge cases, or touch files you never intended to change. By the time you notice the error, the agent has written to disk and the change is difficult to reverse. A single unplanned decision cascades into a flawed feature.

## How it works

Separate planning (reasoning, problem analysis, strategy) from execution (implementation of that strategy). The Planner role analyzes the problem, studies the codebase, considers constraints, and produces a written plan (file map, test criteria, change order). The Executor then implements that specific plan step-by-step with no deviation.

This mirrors how human engineering works: spend time getting the design right, then build it. The pattern also scales: planning is cheap compute (reasoning-heavy), execution can use cheaper models once a plan is locked down.

## Setup

1. **Create a planning gate:** Direct the agent to read files, analyze requirements, and produce a written plan before making any changes. Require human approval before proceeding. Example: "Analyze these files. Design a plan to add feature X. Map out which files change and in what order. Do not implement yet."

2. **Isolate planning from code:** Run planning in a read-only context if your tooling supports it (e.g., Claude Code's Plan Mode). The agent reads freely but cannot write.

3. **Execute from the plan:** Once approved, give the executor agent the plan as context. Instruct: "Implement this plan step-by-step. After each file, run tests before moving to the next."

4. **Use Research-Plan-Implement if needed:** For complex features, expand to three phases: research (gather context), plan (strategy), implement (code).

## When to use / when NOT

**Use when:**
- Feature is non-trivial (affects multiple files, unclear scope)
- Risk of touching wrong code is high
- Human approval gates are required
- Multiple passes by different agents

**Skip when:**
- Bug fix is tiny (one-liner)
- Task is exploratory or one-shot
- You're happy debugging and reverting

## Tradeoffs

**Wins:** Predictable output, reviewable before execution, can catch design errors early, enables cheaper executor models.

**Costs:** Slower for simple tasks, adds latency (plan review wait), requires discipline to not deviate mid-execution.

## Example

```
User: "Add JWT authentication to the API"

Phase 1 (Plan):
Agent reads auth config, route handlers, middleware stack.
Agent produces:
  - Which files change: auth.py, middleware.py, tests/auth_test.py
  - Order: middleware first, then handlers, then tests
  - Assumptions: JWT secret stored in env, refresh token stored in Redis
  
User approves plan.

Phase 2 (Execute):
Agent: "Updating middleware.py..."
  → Changes file, runs tests: pass
  → Commits
Agent: "Updating auth.py..."
  → Changes file, runs tests: pass
  → Commits
Agent: "Adding tests..."
  → Adds tests, runs suite: pass
  → Commits
```

## Notes & links

- Claude Code built-in Plan Mode enforces read-only planning (write tools unavailable)
- Measured benefit: Plan-and-Execute achieves 92% task completion with 3.6× speedup vs. reactive approaches
- Research-Plan-Implement splits the problem into three: gather context → design solution → code it
- Avoid "plausible but wrong" plans: require explicit sign-off before execution
