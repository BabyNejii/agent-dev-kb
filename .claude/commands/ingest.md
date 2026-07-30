---
description: Sweep sources and draft new KB technique entries for review (Haiku-powered, cheap)
argument-hint: "[focus] e.g. tier1 | since 2026-07-28 | mcp servers | integration"
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

You are running the **manual ingestion pipeline** for the agent-dev-kb knowledge base.
KB root: this repository (paths below are relative to it).

Focus for this run (optional; empty = general sweep of all tiers): **$ARGUMENTS**

## Cost rule (important)
Do the expensive work with **Haiku sub-agents**. Spawn them via the `Agent` tool with
`model: "haiku"` and `subagent_type: "general-purpose"`. They fetch, read, and draft —
so long web content never enters your (orchestrator) context. YOU only orchestrate,
dedupe, and validate. Do not fetch pages yourself unless a Haiku agent fails.

## Steps

1. **Load state (cheap).** Read:
   - `TAXONOMY.md` (schema contract)
   - `sources.md` (watchlist + filter rules)
   - `index/index.json` (existing entries — for dedupe). If it's missing,
     run `python tools/build_index.py` first.
   Build a set of existing `id`s so agents can avoid duplicates.

2. **Sweep (Haiku, parallel).** Spawn one Haiku agent per relevant slice — by source
   tier from `sources.md`, or by category, or narrowed to `$ARGUMENTS` if given.
   Each agent must:
   - Research REAL, current software-development agent techniques (WebSearch + WebFetch).
   - Follow the frontmatter schema in TAXONOMY.md EXACTLY.
   - Set `confidence`: `reported` for docs/github/paper, `speculative` for blog/social.
     NEVER `verified` (only a human promotes to verified).
   - Write drafts to `_inbox/<id>.md` (the quarantine folder — NOT
     directly into techniques/).
   - Skip any candidate whose `id` already exists in the index (pass the agent that list).
   - Return only a SHORT bullet list of ids drafted — no file contents.

3. **Dedupe & reconcile (you).** Read the drafts in `_inbox/`. For each:
   - If it duplicates or is weaker than an existing entry → delete it (or note it as an
     UPDATE to the existing file instead).
   - If it contradicts/supersedes an existing entry → note the relationship.
   - Fix any schema violations, thin bodies, or over-confident ratings.

4. **Index & report (cheap).** Run `python tools/build_index.py`.
   Then show the user a compact summary table: id | category | maturity | confidence | 1-line,
   grouped as NEW / UPDATE / SKIPPED(reason). Tell them the drafts are in `_inbox/`
   awaiting their review, and that they move approved ones into `techniques/<category>/`.

## Reminder
Automation PROPOSES; the human KEEPS. Never move drafts out of `_inbox/` into
`techniques/` yourself unless the user explicitly says so.
