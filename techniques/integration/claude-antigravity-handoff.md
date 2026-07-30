---
id: claude-antigravity-handoff
title: Claude ↔ Antigravity task handoff
category: integration
ecosystems: [claude-code, antigravity]
problem: You use both Claude Code and Antigravity CLI, but work and context don't flow between them, so you re-explain the task in each.
maturity: experimental
confidence: speculative
effort_to_adopt: medium
works_with: [shared-context-file-handoff, mcp-as-integration-layer]
supersedes: []
sources:
  - {url: "REPLACE-with-antigravity-docs", kind: docs, date: 2026-07-28}
added: 2026-07-28
updated: 2026-07-28
---

## Problem
Two capable agents, no shared memory. Switching tools means re-establishing the
goal, the constraints, and what's already been tried.

## How it works
Use a **shared, on-disk handoff artifact** as the interchange format — a single
markdown/JSON file both agents read and write: current goal, decisions made,
open questions, and "next action for the other agent." Whichever agent is active
appends its progress; the other picks up from the file instead of from scratch.

## Setup
1. Define a fixed handoff schema (goal / state / decisions / next-step / owner).
2. Have each agent read it on start and update it on stop.
3. Optionally wire it through an MCP server so both read/write via a tool rather
   than raw file edits — see [[mcp-as-integration-layer]].

## When to use / when NOT
- USE when you genuinely alternate between the two tools on the same task.
- NOT if one tool can do the whole job — a handoff adds coordination cost for no gain.

## Tradeoffs
Simplicity (a shared file) vs. robustness (an MCP-mediated channel). Start with
the file; graduate to MCP if drift/conflicts appear.

## Example
`HANDOFF.md` with a `next-step` field; Antigravity does UI scaffolding, records
"tests needed for LoginForm", Claude picks that up and writes them.

## Notes & links
This is a placeholder pattern to be verified against real Antigravity capabilities —
confidence stays `speculative` until tested. Related: [[shared-context-file-handoff]].
