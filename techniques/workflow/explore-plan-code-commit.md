---
id: explore-plan-code-commit
title: Explore-Plan-Code-Commit workflow for agent tasks
category: workflow
ecosystems: [claude-code]
problem: Ad-hoc agent direction produces inconsistent results and wasted exploration
maturity: emerging
confidence: reported
effort_to_adopt: low
works_with: [plan-then-execute, checkpoint-commit-discipline]
supersedes: []
sources:
  - {url: "https://www.openhands.dev/blog/claude-code-best-practices-agentic-coding", kind: blog, date: "2026-07-28"}
  - {url: "https://dev.to/galian/claude-code-workflow-best-practices-that-ship-code-na", kind: blog, date: "2026-07-28"}
  - {url: "https://www.ayautomate.com/blog/best-claude-code-workflows", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Agents given a task description often jump to implementation without understanding the existing codebase, leading to redundant code, missed dependencies, or broken assumptions.

## How it works

A structured four-phase workflow:

1. **Explore:** Agent reads codebase to understand structure, naming patterns, existing solutions
2. **Plan:** Agent produces a written plan of what to change and why (without editing)
3. **Code:** Agent implements the plan
4. **Commit:** Agent commits changes with clear messages

Each phase has specific goals and prevents the agent from making decisions on incomplete information.

## Setup

1. **Phase 1 — Explore (Read-only):**
   ```
   Agent task: "Explore this codebase. Read:
     - File structure (main directories)
     - Key modules and what they do
     - Patterns (naming, structure, dependencies)
     - Related code to what I'm asking you to build
   
   Report: 3-5 paragraphs on what you learned. Don't code yet."
   ```

2. **Phase 2 — Plan (Read-only, with user feedback):**
   ```
   Agent task: "Based on your exploration, plan how to [feature]. Produce:
     - Which files change and why
     - New files (if any)
     - Dependencies to add
     - Tests needed
     - Edge cases to handle
   
   Do not implement yet."
   
   Human: Reviews plan, suggests changes, approves.
   ```

3. **Phase 3 — Code:**
   ```
   Agent task: "Implement this plan exactly:
     [paste approved plan]
   
   After each file, run tests. If tests fail, debug and fix.
   Proceed to next file only when tests pass."
   ```

4. **Phase 4 — Commit:**
   ```
   Agent automatically commits after each passing test:
   
   git commit -m "feat: add user authentication
   
   - Add JWT verification middleware
   - Add /auth/login endpoint
   - Extends existing middleware pattern"
   ```

## When to use / when NOT

**Use when:**
- Feature is multi-step
- Codebase is large or unfamiliar
- You want a checkpoint before implementation
- Risk of missing context is high

**Skip when:**
- Task is tiny (one-liner)
- You already understand the changes needed
- You're spiking/exploring

## Tradeoffs

**Wins:** Consistent results, prevents missed context, agent learns patterns before coding, reviewable before execution.

**Costs:** Slower than direct coding, adds latency (exploration + plan review), only helpful if plan actually improves execution.

## Example

```
User: "Add password reset flow to the auth system"

Phase 1 — Explore:
Agent reads auth/ directory, finds:
  - jwt.py handles token creation
  - middleware.py validates tokens on requests
  - /auth/login already exists
  - Tests in tests/auth_test.py
  - Config uses env vars

Agent reports: "System uses JWT, stateless auth. 
I should add a reset_token() function, /auth/reset endpoint,
and a /auth/confirm-reset endpoint. Existing patterns: 
endpoints return JSON with status, errors use exceptions."

Phase 2 — Plan:
Agent proposes:
  1. Modify jwt.py: add reset_token() with short expiry
  2. Add /auth/reset endpoint (email address only)
  3. Add /auth/confirm-reset endpoint (reset_token + new password)
  4. Add tests covering success, expired token, invalid token

User approves: "Good. Also add rate limiting to /auth/reset."
Agent updates plan.

Phase 3 — Code:
Agent modifies jwt.py, runs tests → pass
Agent adds /auth/reset endpoint, runs tests → pass
Agent adds rate limiting, runs tests → pass
Agent adds /auth/confirm-reset, runs tests → pass
Agent adds test coverage, runs tests → pass

Phase 4 — Commit:
Agent creates atomic commits:
  - "feat: add JWT reset token generation"
  - "feat: add /auth/reset endpoint with rate limiting"
  - "feat: add /auth/confirm-reset endpoint"
  - "test: add password reset flow integration tests"
```

## Notes & links

- **Timing:** Exploration typically takes 2-5 minutes, planning 5-10 minutes, code 15-30 minutes (depending on complexity)
- **Tool support:** Claude Code integrates well with this pattern; Plan Mode enforces read-only phases naturally
- **Related patterns:** This is a simplified version of "Research-Plan-Implement" (with research = explore, plan = plan, implement = code)
- **Best practice:** After exploration, ask the agent to list assumptions before planning (forces explicit reasoning)
