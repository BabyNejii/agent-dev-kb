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

## Source mapping

### `/save-tokens`
- **verified:** [[claude-code-context-window]], [[subagent-fan-out]],
  [[building-custom-subagents]], [[path-scoped-rules]]
- *reported (supporting detail only):* [[prompt-caching-with-claude-api]],
  [[context-compaction-beta]]

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

## Verified entries deliberately NOT installed

- [[claude-code-hooks-tool-lifecycle]] - hook authoring and `settings.json` editing are already
  covered by the built-in `update-config` skill. Installing a second one would duplicate it,
  and two skills competing for the same trigger is worse than one.

That accounts for all 14 `verified` entries: 13 back a skill, 1 was intentionally skipped.

## Keeping this in sync

When an entry is promoted to `verified`, consider whether it strengthens an existing skill
rather than justifying a new one - grouped skills beat many thin ones. After editing a skill,
re-run `install.ps1` in the claude-setup checkout to redeploy, then `doctor.ps1` to verify.

Check the current confidence of any entry named above with:

```
python tools/query.py --confidence verified
```
