# Ingestion runbook (manual trigger)

Run this when you want to pull new techniques into the KB. It's a manual pipeline
for now — no scheduler. Point an agent at this file, or follow it yourself.

## Contract

- **Automation proposes; a human keeps.** New entries land for review, not merged silently.
- New entries are `confidence: reported` (from docs/GitHub) or `speculative` (blog/social).
- Prefer updating an existing entry over adding a near-duplicate.

## Pipeline (model-split for cost)

1. **Sweep (Haiku 4.5)** — for each source in `sources.md`, fetch recent items and
   extract candidate techniques into the frontmatter schema (`TAXONOMY.md`).
   Mechanical extraction; cheap model is enough.

2. **Filter & dedupe (Sonnet 5)** — drop items that aren't software-dev agent
   techniques; drop pure announcements; match candidates against existing `id`s in
   `index/index.json`. Mark each: NEW / UPDATE(existing-id) / SKIP(reason).

3. **Synthesize & reconcile (Opus 4.8)** — for NEW/UPDATE survivors, write the full
   entry body. Check for contradiction/supersession with existing entries. Set
   `maturity`/`confidence` conservatively. Assign the right category folder.

4. **Stage for review** — write proposed files into `techniques/<category>/` (or a
   `_inbox/` folder if you prefer to quarantine). Then:
   - `python tools/build_index.py` to refresh the index.
   - Review the diffs. Keep, edit, or delete. Promote `confidence` only after you trust it.

## Suggested one-shot invocation

> Read `agent-dev-kb/TAXONOMY.md`, `sources.md`, and `index/index.json`. Sweep the
> Tier-1 and Tier-2 sources for new software-development agent techniques since
> {date}. For each: NEW, UPDATE, or SKIP. Write NEW/UPDATE entries as files under
> the correct category, following the schema, conservative on maturity/confidence.
> Then run build_index.py and show me the diff summary. Do not overwrite my edits.

For the big first-time population, use the `deep-research` skill or a `Workflow`
fan-out instead of a single pass — it covers far more ground.
