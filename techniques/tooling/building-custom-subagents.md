---
id: building-custom-subagents
title: Building Custom Subagents for Focused Tasks
category: tooling
ecosystems: [claude-code]
problem: Large tasks flood main context with exploration noise; subagents preserve context by delegating focused work.
maturity: established
confidence: verified
effort_to_adopt: low
works_with: []
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/sub-agents", kind: docs, date: "2026-07-28"}
  - {url: "https://www.digitalapplied.com/blog/build-claude-code-custom-subagent-step-by-step-2026", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

When Claude handles research, refactoring, code review, or testing in the main session, it floods context with intermediate logs, file excerpts, and search results the main session won't reference again. Subagents solve this by running focused tasks in isolated context windows — the subagent explores, summarizes, and returns only the result.

## How it works

A subagent is a specialized agent running in its own context window with:
- A custom system prompt (focused instructions)
- Specific tool access (enforce safety/focus)
- Independent permissions (ask/allow/deny separately)
- A clean context (no main session clutter)

When Claude detects a task matching a subagent's description, it delegates to the subagent. The subagent executes independently and returns a summary or result. The main session sees only the final output, not the intermediate exploration.

Example: Research subagent for fact-checking — when the main session needs to verify a claim, it spawns the research subagent, which searches, fetches sources, and returns a summary. The main session's context stays clean.

## Setup

**1. Create a subagent file**

Subagents are Markdown files with YAML frontmatter. Create at:
- Project scope: `.claude/agents/<name>.md`
- User scope: `~/.claude/agents/<name>.md`

```markdown
---
name: research
description: Research and fact-check claims using web search and document fetching. Use this agent when you need to verify a statement, gather background info, or investigate a topic in depth without flooding the main context with search results.
tools:
  - WebSearch
  - WebFetch
  - Read
  - Glob
  - Grep
model: claude-haiku-4-5-20251001
permissionMode: allow
---

# Research Agent

You specialize in researching topics, verifying claims, and gathering evidence from authoritative sources.

## Your role

1. **Take a claim or topic** from the main session
2. **Search for evidence** using web search and document fetching
3. **Verify sources** — prefer official docs, published papers, and reputable outlets
4. **Synthesize findings** into a concise summary (max 3 paragraphs)
5. **Return only the summary** — the main session doesn't care about intermediate searches

## Constraints

- Max 3-5 web searches per task (be efficient)
- Prefer official docs over blogs
- Include source URLs in your summary
- Be concise — the main session needs clarity, not exhaustive research
```

**2. Configure tool access**

The `tools` field restricts which tools a subagent can use. This enforces focus and safety:

```yaml
tools:
  - WebSearch
  - WebFetch
  - Read
```

Omit `tools` to allow all tools. Common patterns:
- **Research agent**: WebSearch, WebFetch, Read, Glob, Grep (read-only, safe exploration)
- **Code review agent**: Read, Glob, Grep (read-only, no execution)
- **Refactoring agent**: Read, Edit, Bash, Glob (full write access with automation)
- **Testing agent**: Read, Bash, Glob (test execution only)

**3. Select a cost-conscious model**

Subagents are separate billing. Use faster, cheaper models for simple tasks:

```yaml
model: claude-haiku-4-5-20251001    # Fast, cheap; good for focused, constrained tasks
model: claude-opus-5                 # Powerful; use for complex reasoning or ambiguous tasks
```

Haiku is 10x cheaper than Opus and sufficient for most delegated work (research, code search, simple reviews).

**4. Set permission mode for autonomy**

Control whether the subagent can execute tools without asking:

```yaml
permissionMode: allow      # Tools execute silently (full autonomy)
permissionMode: ask        # Ask before each tool (restrictive, slower)
permissionMode: deny       # Never execute; raise all to main session (defeats purpose)
```

For trusted, focused agents (research, search), use `allow`. For agents that modify state (refactoring), use `ask`.

**5. Write a focused system prompt**

The markdown body (after frontmatter) is the agent's system prompt. Keep it:
- **Concise**: 5-10 sentences max (longer prompts waste tokens)
- **Task-focused**: Clear constraints and expected output
- **Reminder-driven**: Tell it what matters and what doesn't

Good research agent prompt:

```markdown
# Research Agent

You specialize in verifying claims and gathering evidence from authoritative sources.

## Task

The main session asks you to research a claim or topic. Your job:
1. Search for evidence using web search
2. Fetch authoritative sources (official docs, papers, published articles)
3. Summarize findings in 2-3 paragraphs
4. Include source URLs

Keep it brief — the main session will read your summary once. No need for exhaustive detail.
```

**6. Describe the agent for auto-delegation**

The `description` field tells Claude when to delegate to this agent. Make it specific:

```yaml
description: Research and fact-check claims using web search. Delegates when the main session needs to verify a statement or gather background information without exploring in the main context.
```

Clear descriptions enable auto-delegation; vague ones never trigger.

**7. (Optional) Create supporting files**

Subagents can use supporting files (templates, examples, scripts):

```
.claude/agents/
  code-review/
    code-review.md              # Agent definition
    REVIEW_CHECKLIST.md         # Template: security, performance, style
    examples/
      good_review.md
      bad_review.md
```

Reference these in your prompt:

```markdown
---
name: code-review
...
---

# Code Review Agent

Review code submissions. Use the checklist in REVIEW_CHECKLIST.md and the examples in examples/ as reference.
```

## When to use / when NOT

**Delegate to subagents:**
- Research and fact-checking (main session doesn't care about search logs)
- Code review (read-only exploration; main session needs only the summary)
- Refactoring (agent makes sweeping changes; main session needs only "refactored and tested")
- Testing (agent runs suite; main session needs only "tests passed" or failure summary)
- File searching (agent explores codebase; main session needs only results)

**Keep in main session:**
- User-facing interactions (agent needs rich context from user)
- Decision-making (main session should see alternatives)
- Writing code the user will modify (user needs to understand each change)

## Tradeoffs

- **Context isolation vs. context sharing**: Subagents have fresh context (saves tokens) but can't reference main session findings. Use when delegation is clean; avoid for tasks requiring prior context.
- **Model cost vs. capability**: Haiku is 10x cheaper but less capable. Opus is better for ambiguous/complex tasks but costs more.
- **Tool restrictions vs. autonomy**: Restricted tools (research agent can only read) enforce safety but slow execution if the agent needs to ask before each call.

## Example

A production code-review subagent:

```markdown
---
name: code-review
description: Review code for quality, security, and test coverage. Delegates when the main session needs a second opinion on code changes before merging.
tools:
  - Read
  - Glob
  - Grep
model: claude-opus-5
permissionMode: allow
---

# Code Review Subagent

You are an expert code reviewer specializing in security, performance, and maintainability.

## Your task

The main session submits code (file paths or diffs) for review. Analyze thoroughly and return:

1. **Security issues** (first pass — highest priority)
2. **Performance concerns** (algorithmic, resource usage)
3. **Maintainability** (clarity, test coverage, conventions)
4. **Praise** (what's good; reinforce good patterns)

## Review checklist

See REVIEW_CHECKLIST.md for specifics by language.

## Output format

Structured summary:
- Security: [list issues or "✓ no issues found"]
- Performance: [list concerns or "✓ acceptable"]
- Maintainability: [list items or "✓ well structured"]
- Approval: APPROVED / REQUEST CHANGES / NEEDS DISCUSSION

Keep it concise — the main session reads this once before acting.
```

## Notes & links

- **Built-in subagents**: Claude Code includes pre-built agents (Explore, Plan, general-purpose). You can't configure these, but you can see how they work as templates.
- **Context window visualization**: See the [Claude Code context window docs](https://code.claude.com/docs/en/context-window) for a walkthrough showing how subagents preserve main session context.
- **Discoverability**: Subagents with clear, specific descriptions auto-delegate when relevant. Vague descriptions (e.g., "helper agent") don't trigger auto-delegation.
- **Team sharing**: Project-scoped subagents (`.claude/agents/`) can be checked into version control so your team reuses them.
- **CLI management**: Run `claude agents` from the CLI to list configured agents and see overrides.
