# Skills distilled from this knowledge base

Five entries in this KB graduated into **installed Claude Code skills**. They live at
`~/.claude/skills/` and are deployed by a sibling repo's installer:
[BabyNejii/claude-setup](https://github.com/BabyNejii/claude-setup) (`install.ps1`, skill
sources in `claude/skills/`).

Full plain-language explainer: **`SKILLS.md` in that repo** (canonical - kept in one place
rather than duplicated). This file records *which entries back which skill*, so you can trace a
skill's claim to its source and know how much to trust it.

## Promotion rule

Only entries at `confidence: verified` - core mechanism confirmed against official
Anthropic/Claude/MCP documentation - were used as a skill's **backbone**. Entries at `reported`
could contribute supporting detail but never a skill's central claim. Nothing `speculative` was
used at all.

## Skills at a glance

| Skill | Use when |
|---|---|
| `/save-tokens` | A task will be expensive; context filling up; auditing a project for waste |
| `/delegate-work` | Work spans many files/subsystems; bulk generation; multi-angle review |
| `/design-mcp-tools` | Building or reviewing an MCP server or tool definition |
| `/project-instructions` | CLAUDE.md ignored or too long; path-scoped rules; monorepo setup |
| `/shape-llm-output` | Need parseable/consistent output from a model call |
| `/operate-agents` | Guarding a run, runaway loop, "what did it do", telemetry, cost attribution |

## Source mapping

### `/save-tokens`
- **verified:** [[claude-code-context-window]], [[subagent-fan-out]],
  [[building-custom-subagents]], [[path-scoped-rules]], [[token-counting-api-preflighting]],
  [[batch-api-cost-reduction]], [[claude-code-jsonl-session-logs]]
- *reported (supporting detail only):* [[prompt-caching-with-claude-api]],
  [[context-compaction-beta]], [[progressive-disclosure-lazy-context]],
  [[agent-context-lifecycle-management]]

### `/delegate-work`
- **verified:** [[subagent-fan-out]], [[agent-teams-coordination]],
  [[building-custom-subagents]], [[subagent-test-generation-bulk]]
- *reported (supporting detail only):* [[git-worktree-isolation]], [[adversarial-code-review]]

### `/design-mcp-tools`
- **verified:** [[mcp-tool-design-principles]], [[claude-tool-naming-descriptions]],
  [[mcp-error-handling-model-recovery]], [[mcp-tool-standardization]]
- *reported (supporting detail only):* [[mcp-tool-execution-sandboxing]]

### `/project-instructions`
- **verified:** [[path-scoped-rules]], [[claude-code-context-window]]
- *reported (supporting detail only):* [[claude-md-persistent-memory]],
  [[instruction-hierarchy-layering]], [[negative-instructions-effectiveness]]

### `/shape-llm-output`
- **verified:** [[structured-outputs-api]], [[xml-structured-prompting]], [[few-shot-examples]]

### `/operate-agents`
- **verified:** [[pretooluse-guards-dangerous-operations]],
  [[permission-deny-rules-resource-isolation]], [[postoolbatch-circuit-breaker-parallel-tasks]],
  [[agent-sdk-otel-observability]], [[claude-code-jsonl-session-logs]],
  [[token-counting-api-preflighting]], [[admin-cost-report-api]]
- *reported (supporting detail only):* [[action-cache-replay]], [[cost-budgeted-routing]],
  [[multi-agent-cost-attribution-sdk]], [[mcp-tool-execution-sandboxing]]

Seven verified entries back this one - the strongest backbone of any skill here, because Claude
Code documents guards, telemetry, and cost measurement natively.

## Verified entries deliberately NOT installed

- [[claude-code-hooks-tool-lifecycle]] - the *mechanics* of authoring hooks and editing
  `settings.json` are covered by the built-in `update-config` skill, and the *safety use* of hooks
  is now covered by `/operate-agents`. A third skill on the same surface would just compete for
  the same trigger.
- Remaining `verified` entries not backing a skill are single-topic ones whose content lives
  inside a broader skill rather than justifying its own (e.g. [[mcp-tool-standardization]],
  [[agent-teams-coordination]] both feed `/delegate-work` and `/design-mcp-tools`).

Run `python tools/query.py --confidence verified` for the current authoritative list; the counts
above go stale as entries are promoted.

## Keeping this in sync

When an entry is promoted to `verified`, consider whether it strengthens an existing skill
rather than justifying a new one - grouped skills beat many thin ones. After editing a skill,
re-run `install.ps1` in the claude-setup checkout to redeploy, then `doctor.ps1` to verify.

Check the current confidence of any entry named above with:

```
python tools/query.py --confidence verified
```
