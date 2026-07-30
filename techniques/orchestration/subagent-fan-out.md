---
id: subagent-fan-out
title: Sub-agent fan-out for parallel exploration & review
category: orchestration
ecosystems: [claude-code, claude-sdk]
problem: A single agent's context fills up and serializes work that is naturally parallel (searching many files, reviewing many dimensions).
maturity: established
confidence: verified
effort_to_adopt: low
works_with: [supervisor-pattern, adversarial-code-review]
supersedes: []
sources:
  - {url: "https://docs.claude.com/en/docs/claude-code", kind: docs, date: 2026-07-28}
added: 2026-07-28
updated: 2026-07-28
---

## Problem
When one agent must read across many files or evaluate a change along several
independent dimensions, doing it inline both bloats the main context and forces
sequential work. The main agent ends up holding raw file dumps it doesn't need.

## How it works
Spawn several read-only sub-agents, each scoped to one slice of the work, and
keep only their *conclusions* — not the files they read. The sub-agent's context
is discarded when it returns; the orchestrator keeps a compact result.

Two shapes:
- **Fan-out search:** N explorers, each searching a different subsystem/angle,
  return findings. Good when one search strategy won't surface everything.
- **Dimension review:** one reviewer per concern (correctness, security, perf,
  tests), each returning structured findings, then a synthesis step.

## Setup
In Claude Code, launch multiple `Agent` calls **in a single message** so they run
concurrently. For deterministic multi-stage fan-out, use the `Workflow` tool's
`parallel()` / `pipeline()` primitives and split models by stage (cheap model
extracts, expensive model synthesizes).

## When to use / when NOT
- USE when the work is decomposable and you only need the conclusion, not the raw material.
- USE when reviewing along independent axes.
- NOT for a single-fact lookup where you already know the file — just read it.
- NOT when stages are truly dependent (one needs another's full output) — that serializes anyway.

## Tradeoffs
More agents = more tokens and coordination overhead. The win is wall-clock time
and a clean orchestrator context, not fewer tokens.

## Example
"Review this diff" → 4 parallel reviewers (bugs / perf / tests / style) →
1 synthesis agent that dedupes and ranks. See [[adversarial-code-review]] for the verify step.

## Notes & links
Pairs naturally with [[supervisor-pattern]] for the deterministic version.
