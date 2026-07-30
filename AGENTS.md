# AGENTS.md — onboarding for agents working in this repo

Read this first. It gets you productive in `agent-dev-kb` in ~60 seconds.
(Human-oriented overview is in `README.md`; the exact schema is in `TAXONOMY.md`.)

## What this repo is

A curated knowledge base of **techniques for building software with AI agents**.
Claude-primary (Claude Code / Agent SDK / API), with **cross-agent integration**
(Claude ↔ Antigravity, MCP) as a headline theme. One markdown file = one technique.

It serves two readers at once:
- **Humans** read the markdown body.
- **Agents** parse the YAML frontmatter and can load an entry as actionable context.

## Layout

```
README.md      human overview            TAXONOMY.md   the schema contract (authoritative)
SKILLS.md      which entries became installed Claude Code skills, + the promotion rule
sources.md     ingestion watchlist       INGEST.md     manual ingestion pipeline
techniques/<category>/<id>.md            index/index.json   generated; do not hand-edit
tools/build_index.py  validate + regenerate index    tools/query.py   filter entries
_inbox/        quarantine for un-reviewed drafts     _verify/  verification audit trail
.claude/commands/ingest.md               → the /ingest slash command
```

Categories: `orchestration`, `context`, `workflow`, `integration`, `tooling`,
`prompting`, `eval`, `codebase-ops`.

## How to do the common tasks

**Find a technique** — use the query tool (fastest, no context cost):
```
python tools/query.py --stats                              # distribution summary
python tools/query.py --category eval --confidence verified
python tools/query.py --ecosystem antigravity
python tools/query.py --search worktree --full             # + problem line and path
python tools/query.py --min-confidence reported            # this level and better
python tools/query.py --paths --category tooling           # bare paths, pipe-friendly
```
It reads `index/index.json`, so rebuild the index first if entries changed.
You can also grep `techniques/` or read `index/index.json` directly.

**Add an entry** — copy `techniques/_TEMPLATE.md`, fill it per `TAXONOMY.md`, save as
`techniques/<category>/<id>.md` where `id` == filename == the `id:` field. Then run
`python tools/build_index.py`.

**Bulk-ingest new techniques** — follow `INGEST.md` (or run `/ingest`). Drafts go to
`_inbox/` for review; they are NOT part of the KB until a human moves them into
`techniques/`.

**Validate** — `python tools/build_index.py` reports schema errors, id/filename
mismatches, and per-category counts. Run it after any change.

## Rules (do not skip)

1. **Automation proposes; a human keeps.** Never move drafts out of `_inbox/` into
   `techniques/` on your own. Never delete or overwrite a reviewed entry without being asked.
2. **Confidence honesty.** `verified` requires a Tier-1 official-doc source
   (docs.anthropic.com, docs.claude.com, platform.claude.com, code.claude.com,
   modelcontextprotocol.io, official Antigravity docs). Blog/community/paper → `reported`.
   Unconfirmable → `speculative`. Never invent a source URL.
3. **Rebuild the index** (`python tools/build_index.py`) after adding/editing/removing entries.
4. **Prefer updating over duplicating.** Check `index/index.json` for an existing `id`
   first. If a technique replaces another, set `supersedes` and mark the old one `deprecated`.
5. **Cost discipline.** For any research sweep, do the fetching/drafting with **Haiku
   sub-agents** (they write files directly); reserve the expensive model for
   dedupe/synthesis/validation. This is the pattern the whole KB was built with.
6. **Links.** Relate entries with `[[other-id]]`. A link to a not-yet-written id is an
   allowed "write this next" marker — but don't leave broken `works_with` refs in frontmatter.

## Current status (2026-07-28)

- ~49 entries across all 8 categories (first sweep, drafted by parallel Haiku agents).
- Most are `confidence: reported`; a verification pass promotes/downgrades from there.
- Known gaps (referenced but unwritten — good first entries): `claude-code-context-window`,
  `path-scoped-rules`.
