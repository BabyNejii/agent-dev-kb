---
id: progressive-disclosure-lazy-context
title: Progressive disclosure — load context names first, full content on demand
category: context
ecosystems: [claude-code, claude-sdk, claude-api, generic]
problem: Loading all context upfront (all skill definitions, complete tool schemas, full documentation) wastes tokens on content agents may never use
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [mcp-code-api-over-tools, prompt-caching-with-claude-api, filesystem-context-management]
supersedes: []
sources:
  - {url: "https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", kind: github, date: 2026-07-30}
  - {url: "https://github.com/Meirtz/Awesome-Context-Engineering", kind: github, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

Agent systems often load all available context at startup: every tool definition, every skill description, every reference document, every API schema. But in a large project (100+ tools, 50+ skills, extensive API docs), most of that context is never used on any given task, and it consumes a meaningful slice of the window before any actual work begins. Measure it on your own setup rather than assuming a figure. Progressive disclosure solves this: expose **names and short descriptions first**, and load **full content only when needed**.

## How it works

Organize context in layers, exposing progressively richer detail on demand:

1. **Layer 1 (Names & summary)**: Agents see a list of skill/tool names and 1-2 sentence descriptions.
   - Example: `Tool: "code-search"` — "Find function/class definitions by name or pattern."

2. **Layer 2 (Details)**: When an agent decides to use a tool, load its full schema/documentation.
   - Example: Full parameters, return types, error codes, constraints.

3. **Layer 3 (Examples & context)**: Load concrete examples, related tools, and contextual guides only for active paths.
   - Example: Code snippets, ADRs, related technique pages.

**File structure pattern** (from digital-brain / Agent-Skills approach):
```
SKILL.md              # skill name, summary, triggers (what activates this skill)
MODULE.md             # (optional) deeper module docs; loads if the skill activates
scripts/              # (optional) code; loads if referenced
references/           # (optional) supporting materials; loads if requested
```

The key: **SKILL.md stays under 500 lines** (or <5 KB). Details live elsewhere and load on demand.

## Setup

For Claude Code projects:

1. **Structure skills with progressive loading**:
   ```
   .claude/skills/
     ├── refactor-safety/
     │   ├── SKILL.md           # 50 lines: what, when, constraints
     │   ├── DETAILS.md         # full methodology, examples
     │   ├── scripts/           # code referenced from DETAILS
     │   └── references/        # related techniques
   ```

2. **SKILL.md template** (stays brief):
   ```markdown
   # Refactor Safety
   Restructure code with automated test validation and rollback.
   **Triggers**: refactor, safety-first, large-scale change
   **Works with**: checkpoint-commit-discipline, human-in-loop-review
   
   [Full docs in DETAILS.md]
   ```

3. **Load strategy in agent instructions**:
   > "When asked about a skill, describe what you know from SKILL.md summary. If the user asks for details or you need to execute it, read the full DETAILS.md."

For API/MCP contexts:

4. **Expose tool definitions progressively**:
   - Start: tool names + brief descriptions
   - On activation: full schema (parameters, return type, error handling)
   - On execution: usage examples, caveats, constraints

## When to use / when NOT

**Use when:**
- Projects have 30+ tools, skills, or context modules.
- Not all context is relevant to every task (large, specialized projects).
- Context window is constrained or budget-conscious.
- You want agents to discover capabilities on-demand rather than memorize a reference.

**Don't use when:**
- Context is small (< 50 tools or < 20 KB); overhead not worth the structure.
- Agents need immediate access to all options (interactive decision-making).
- Latency is critical (each layer-load adds an API call).

## Tradeoffs

| Benefit | Cost |
|---------|------|
| Frees tokens: agents start with summaries (~5KB) instead of full docs (~50KB) | Requires structure; more API calls if agents discover then load |
| Faster startup for agents that use only a subset of tools | Harder to train agents on full capability set upfront |
| Encourages focused tool design (each tool must have a clear summary) | Adds directory structure complexity |
| Scales well as projects grow | Discovery overhead if agents misjudge what they need |

## Example

**Before progressive disclosure** (all context at once):
```
Prompt context: [50 tools × 500 tokens each] + [agent instructions] = 26KB
Agent reads: "Looking for a tool that..." (searches through mental model of 50 tools)
Time to decision: high; many irrelevant options increase confusion
```

**With progressive disclosure** (names first, details on demand):
```
Prompt context: [50 tool summaries × 20 tokens each] + [agent instructions] = 1KB
Agent reads: "I see tools: code-search, test-runner, ... let me check code-search."
Agent calls: "get tool details for code-search"
Response: [full schema for code-search]
Time to decision: lower; agent narrows focus before loading detail
```

## Notes & links

- Similar to [[mcp-code-api-over-tools]] but broader: applies to any context (not just MCP tool definitions). MCP code APIs are one implementation of progressive disclosure specifically for tool schemas.
- Complements [[prompt-caching-with-claude-api]]: progressive disclosure reduces the size of what gets cached; caching then reuses that smaller context across requests.
- Related to [[filesystem-context-management]]: both defer loading non-critical context. Filesystem approach uses the filesystem as the store; progressive disclosure uses the interface (names → details on demand).
- Commonly used in Claude Code projects with deep `.claude/skills/` hierarchies and in LangChain / Letta agent frameworks with lazy-loading memory systems.
