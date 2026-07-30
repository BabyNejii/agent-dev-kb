---
id: checkpoint-commit-discipline
title: Checkpoint and commit discipline for agent-written code
category: workflow
ecosystems: [claude-code, generic]
problem: When agents produce large changes without commits, bugs become hard to isolate and recovery is painful
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [plan-then-execute, iterative-self-refinement, human-in-loop-review]
supersedes: []
sources:
  - {url: "https://understandingdata.com/posts/checkpoint-commit-patterns/", kind: blog, date: "2026-07-28"}
  - {url: "https://www.digitalapplied.com/blog/agent-rollback-checkpoint-patterns-2026-engineering-reference", kind: blog, date: "2026-07-28"}
  - {url: "https://dev.to/teppana88/how-i-validate-quality-when-ai-agents-write-my-code-481c", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

An agent that writes 500 lines across 10 files in a single commit makes debugging impossible: you can't bisect with `git bisect`, you can't cherry-pick a fix, and reverting breaks everything. If one file is wrong, you have to untangle the whole commit.

## How it works

Treat each validated, testable unit of work as a checkpoint. After the agent finishes each unit:
1. Run validation (tests, type checks, linting)
2. If validation passes, commit
3. If validation fails, the agent fixes only that unit (no scope creep)
4. Then move to the next unit

This creates a linear history where every commit is a known-good state and a rollback point.

**Two meanings of "checkpoint":**
- **Git checkpoints:** Small atomic commits in version control (the developer-facing one)
- **Workflow state checkpoints:** Saved execution state for long-running agents that span hours/days (framework-level, used in LangGraph/Temporal)

This guide focuses on git checkpoints for interactive agent coding.

## Setup

1. **Define atomic units:** Before the agent starts, break the feature into small, testable pieces. Examples:
   - Add a new function
   - Refactor one module
   - Add tests for a subsystem
   - Update one route handler

2. **Automate validation after each unit:**
   ```bash
   # After agent modifies a file/function:
   pytest tests/
   mypy src/
   black --check src/
   ```

3. **Enforce feature-branch isolation:** Agent should never work on `main`. Always create a feature branch:
   ```bash
   git checkout -b feature/add-auth
   # Agent works here
   git commit -m "Add JWT middleware"
   git commit -m "Add auth route handler"
   # etc.
   ```

4. **Use git worktrees for parallel work:** If you need to run multiple agent sessions safely:
   ```bash
   git worktree add ../agent-task-1 -b feature/task-1
   # Agent works in isolation, shares .git but has separate branch
   ```

5. **Require commit messages:** Even auto-generated, enforce a pattern (e.g., conventional commits). This creates searchable history. Example: `git commit -m "feat: add JWT verification"`

## When to use / when NOT

**Use when:**
- Feature is multi-step
- You need to revert individual changes
- Multiple people working on related code
- Debugging or bisecting is likely

**Skip when:**
- Trivial, single-file changes
- Personal throwaway code
- Exploring/spiking

## Tradeoffs

**Wins:** Reversible changes, clear history, `git bisect` works, easier code review, containment when things go wrong.

**Costs:** More commits (messier log if you don't squash), slight overhead to validation between commits.

## Example

```
Agent breaks feature into units:
  1. Add JWT secret to config
  2. Add verify_token() function
  3. Add auth middleware
  4. Add /login endpoint
  5. Add tests for auth flow

Agent implements unit 1:
  → Modifies config/settings.py
  → Runs: pytest, mypy, black → all pass
  → Agent commits: "config: add JWT_SECRET env var"

Agent implements unit 2:
  → Adds jwt.py with verify_token()
  → Runs: pytest, mypy, black → all pass
  → Agent commits: "feat: add JWT token verification"

... etc ...

History (clean, bisectable):
  abc1234 config: add JWT_SECRET env var
  def5678 feat: add JWT token verification
  ghi9012 feat: add auth middleware
  jkl3456 feat: add /login endpoint
  mno7890 test: add auth flow integration tests
```

## Notes & links

- Git worktrees are ideal for agent isolation: the agent gets full repo access but its changes stay on a separate branch, zero contact with your working copy
- Atomic commits enable `git bisect` to pinpoint the commit that broke tests
- Modern frameworks (LangGraph, Temporal) have workflow-level checkpointing for long-running agent systems—separate from git commits but same principle
- Conventional commits (feat:, fix:, refactor:) make agent-generated history searchable: `git log --grep="^feat"` finds feature commits only
