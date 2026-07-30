# Taxonomy & entry schema

This file is the contract. Every technique file must conform to it, and the
ingestion pipeline is instructed to follow it. Keep it short and stable —
changing a field here means migrating every entry.

## Frontmatter schema

```yaml
---
id: subagent-fan-out            # kebab-case, unique, == filename without .md
title: Sub-agent fan-out for parallel exploration
category: orchestration         # one of the categories below
ecosystems: [claude-code]       # subset of the ecosystems below
problem: One-line statement of the pain this removes
maturity: emerging              # experimental | emerging | established | deprecated
confidence: reported            # verified | reported | speculative
effort_to_adopt: low            # low | medium | high
works_with: [mcp, workflow-tool]# ids/tags of related techniques (may not exist yet)
supersedes: []                  # ids of entries this replaces
sources:
  - {url: "https://...", kind: docs, date: 2026-07-20}
added: 2026-07-28               # ISO date first added
updated: 2026-07-28             # ISO date last changed
---
```

### Field vocabularies

**category** (also the folder name):
- `orchestration` — coordinating multiple agents/sub-agents for a coding task
- `context` — managing what's in the model's context: memory, retrieval, large codebases
- `workflow` — end-to-end dev loops (plan → implement → review → test → iterate)
- `integration` — making different agents/tools work together (Claude ↔ Antigravity, MCP, handoffs)
- `tooling` — MCP servers, custom tools, wiring dev tools into an agent
- `prompting` — instructions, CLAUDE.md, skills authoring, output shaping
- `eval` — verifying agent output: review gates, tests, LLM-as-judge, adversarial checks
- `codebase-ops` — large-scale code operations: refactors, migrations, test generation

**ecosystems:** `claude-code`, `claude-sdk`, `claude-api`, `antigravity`, `mcp`, `generic`

**maturity:**
- `experimental` — new, unproven, may not survive
- `emerging` — gaining traction, some real use
- `established` — widely used, dependable
- `deprecated` — superseded or no longer recommended (keep for history; note the replacement)

**confidence** (how much *we* trust the claim):
- `verified` — core mechanism confirmed against an authoritative/primary source
  (official Anthropic/Claude/MCP/Antigravity docs), **or** tested by us in practice.
  A `verified` entry MUST carry at least one Tier-1 official source URL.
- `reported` — a credible but non-authoritative source (blog, community, paper)
  describes it; consistent and plausible, but not confirmed against primary docs.
- `speculative` — plausible/early signal, single weak source, or unconfirmable — treat with caution.

## Body structure

After the frontmatter, use these sections (omit any that don't apply):

```markdown
## Problem
## How it works
## Setup
(concrete steps or code — the part an agent could execute)
## When to use / when NOT
## Tradeoffs
## Example
## Notes & links
(use [[other-id]] to link related entries)
```

## Rules

1. `id` == filename == the `id` field. No collisions.
2. New/unverified entries are `reported` or `speculative`, never `verified`.
   Only a human or a verification pass promotes to `verified`.
3. Prefer updating an existing entry over creating a near-duplicate.
   If a technique replaces another, set `supersedes` and mark the old one `deprecated`.
4. Every entry needs at least one source, except `verified` ones you authored yourself.
