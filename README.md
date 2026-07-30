# agent-dev-kb

A living knowledge base of **techniques for building software with AI agents**.

Claude-primary (it's the strongest coding agent), with **cross-agent integration**
(Claude ↔ Antigravity CLI, MCP bridges, sub-agent handoffs) as a headline theme.

## What goes in here

One markdown file per technique, under `techniques/<category>/<id>.md`.
Each file has machine-readable frontmatter (for agents to load) and a human-readable
body (for you to skim). See `TAXONOMY.md` for the schema and category definitions.

Design goal: an entry should be good enough that an agent could load it as context
and *act* on it, and you could read it and *decide* whether to adopt it.

## How to use it

- **Browse:** open `techniques/` and read. Everything is plain markdown.
- **Query:** `python tools/query.py --stats` for a distribution summary, or filter with
  `--category`, `--confidence`, `--min-confidence`, `--maturity`, `--effort`,
  `--ecosystem`, `--search`. Add `--full` for problem lines, `--paths` for bare paths.
- **Re-index:** `python tools/build_index.py` regenerates `index/index.json` (which
  `query.py` reads) and reports any schema errors. Run it after changing `techniques/`.
- **Add by hand:** copy `techniques/_TEMPLATE.md`, fill it in, drop it in the right
  category folder.
- **Add by pipeline:** run the ingestion runbook in `INGEST.md` (manual trigger).
  It fetches from the sources in `sources.md`, drafts entries, and leaves them for
  you to review before they're kept.

## Output: installed skills

Five entries have graduated into real Claude Code skills, deployed machine-wide by
[BabyNejii/claude-setup](https://github.com/BabyNejii/claude-setup): `/save-tokens`,
`/delegate-work`, `/design-mcp-tools`, `/project-instructions`, `/shape-llm-output`. Only
`verified` entries were allowed to form a skill's backbone. See `SKILLS.md` here for the
entry-to-skill mapping, and that repo's `SKILLS.md` for the plain-language explainer.

This is the point of the KB: entries that prove out become capabilities you actually use.

## Quality model

Every entry carries two trust fields: `maturity` and `confidence`. Automated
additions land as `reported` or `speculative` and stay there until a human (you)
or a verification pass promotes them. **Automation proposes; a human keeps.**

## Layout

```
README.md          this file
TAXONOMY.md        schema spec + category & field vocabulary
sources.md         the watchlist the ingestion pipeline sweeps
INGEST.md          manual-trigger ingestion runbook (the pipeline)
techniques/
  _TEMPLATE.md     blank entry to copy
  <category>/<id>.md
index/
  index.json       generated — do not edit by hand
tools/
  build_index.py   validates entries + regenerates index.json from frontmatter
  query.py         filter/list entries from the index
_verify/           audit trail of fact-check verdicts (provenance; safe to delete)
```
