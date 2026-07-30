# _verify - fact-check audit trail

Raw verdict reports written by the sub-agents that fact-checked each category, one JSON file
per category, plus `zylos-audit.json` for a targeted source audit.

Kept as **provenance**: they record what was checked, against which source, and why an entry
was promoted, kept, downgraded, or corrected. Safe to delete; nothing reads them at runtime.

## These are agent reports, not ground truth

Each file records what a verifier agent *said it did*. The technique files themselves are the
only authority on an entry's current `confidence`.

One known discrepancy: **`context.json` claims four entries were promoted to `verified`
(`prompt-caching-with-claude-api`, `claude-md-persistent-memory`, `auto-memory-for-claude-code`,
`context-compaction-beta`). They were not.** All four are still `confidence: reported` on disk.
The agent reported a change it never saved.

It is left uncorrected on purpose - it is the clearest example in this repo of why the rule is
*check the artefact, not the report about it*. To see the real state of any entry:

```
python tools/query.py --confidence verified
```
