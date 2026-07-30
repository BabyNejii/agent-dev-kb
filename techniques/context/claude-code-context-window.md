---
id: claude-code-context-window
title: Managing Claude Code's context window for long sessions
category: context
ecosystems: [claude-code]
problem: "Sessions accumulate context (files, CLAUDE.md, memory, tool output) and eventually approach limits; poor management wastes tokens or forces suboptimal trade-offs between scope and precision"
maturity: established
confidence: verified
effort_to_adopt: low
works_with: [claude-md-persistent-memory, context-compaction-beta, subagent-fan-out, auto-memory-for-claude-code]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/context-window", kind: docs, date: "2026-07-28"}
  - {url: "https://platform.claude.com/docs/en/build-with-claude/context-windows", kind: docs, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Claude Code sessions have a finite context window—the total tokens available to hold system instructions, conversation history, file reads, and command output. As sessions grow:

- Token consumption compounds: each file read, rule load, and tool execution adds tokens.
- Context rot sets in: Claude's reasoning degrades as window fills (accuracy and recall degrade on longer contexts).
- Sessions either hit the hard limit and stop, or force expensive choices: skip important files, clear history, or drop context.
- Without visibility, developers waste time searching for what went wrong and don't know which reads cost most.

Default window is 200k tokens for most models; newer models support 1M tokens. Managing context is as important as having a large window—curating what's in context matters more than maximizing capacity.

## How it works

Claude Code loads context in this order, before you type anything:

1. **System prompt** (~4,200 tokens): core instructions for behavior, tool use, response formatting. Never visible, always loaded first.
2. **Auto memory** (first 200 lines or 25KB): Claude's notes from prior sessions—build commands it learned, patterns it noticed, mistakes to avoid.
3. **Environment info** (~280 tokens): working directory, platform, shell, OS version, git branch/status/commits.
4. **MCP tool schemas** (~120 tokens deferred): tool names listed; full schemas load on-demand via tool search when needed.
5. **Skill descriptions** (~450 tokens, dropped after `/compact`): one-liners for available skills so Claude knows what it can invoke.
6. **Global CLAUDE.md** (~300+ tokens): user's global preferences from `~/.claude/CLAUDE.md`.
7. **Project CLAUDE.md** (1,800+ tokens): project conventions, build commands, architecture notes from project root.

Then, as work happens:

- **File reads** (typically 1–5k tokens per file): dominate context usage; each file you ask Claude to read enters context completely.
- **Path-scoped rules** (~300 tokens each): load automatically when Claude reads matching files, then stay in context.
- **Command output** (~600–2k tokens): tool results, test output, grep output.
- **Hooks** (~100–120 tokens per fire): PostToolUse hooks report output via `additionalContext` JSON; plain stdout goes to debug log, not context.
- **Conversation turns** (your prompts + Claude's responses): visible exchanges accumulate in full.

After `/compact`, most startup content **reloads automatically** (system prompt, project CLAUDE.md, auto memory), but the conversation is replaced with a structured summary (~12% of pre-compact conversation tokens). Skill listings are **not** re-injected after compact.

### Context rot

Accuracy and recall degrade as token count grows—a documented phenomenon. This makes context curation critical: don't just maximize window size, minimize what's in context.

## Setup

**Monitor your current usage:**
```bash
claude /context
```
Live breakdown by category with optimization suggestions. Shows which CLAUDE.md and auto memory files loaded, and per-category token count.

**Edit memory files:**
```bash
claude /memory
```
Open and edit CLAUDE.md and auto memory in your editor.

**Manual compaction with focus:**
```bash
claude /compact focus on the auth bug fix
```
Summarize older exchanges before a long new task. The summary keeps what you choose, not what automatic compaction guesses.

**Clear between unrelated tasks:**
```bash
claude /clear
```
Drop everything and start fresh. Use when switching projects or major contexts. Old conversation crowds out new files and costs tokens on every message.

**Delegate large reads to subagents:**
Use the Agent tool to spawn a research subagent:
```bash
claude
> Use a subagent to research session timeout handling across the codebase, then implement a fix
```
The subagent works in its own separate context window. Large file reads stay out of your main context; only the final summary comes back.

**Optimize CLAUDE.md size:**
- Aim for <200 lines total in project CLAUDE.md; large files hurt adherence.
- Use path-scoped rules for conditional loading—load instructions only when Claude works with matching files.
- Move reference content (README, architecture docs) outside CLAUDE.md; reference with `@path` syntax instead.

## When to use / when NOT

**Use context-window management for:**
- Research-heavy tasks: delegate to subagents to keep large reads isolated.
- Long sessions (>5 exchanges): compact proactively before context affects quality.
- Repeated work on the same codebase: invest in CLAUDE.md so Claude reuses learned patterns.
- Large codebases: use path-scoped rules to load only relevant instructions.

**When NOT to:**
- Short one-off tasks: context pressure is minimal; focus on clarity instead.
- Debugging active issues: compacting mid-investigation loses context; finish, commit, then compact.
- Sensitive data: never put secrets in CLAUDE.md (use `.CLAUDE.local.md` + .gitignore).

## Tradeoffs

**Strengths:**
- Automatic compaction means context limits won't crash sessions—conversation continues.
- Subagent delegation isolates large reads; clean separation of concerns.
- `/context` and `/compact` give visibility and control.
- Project CLAUDE.md persists across sessions; one-time investment, long-term payoff.
- Path-scoped rules load only when relevant.

**Weaknesses:**
- Compaction loses granular history; Claude can reference work but not the exact code read earlier.
- Manual compaction is a speed bump—runs a summarization request (adds latency, uses tokens).
- Skill descriptions don't reload after `/compact`; only skills you invoked are preserved.
- Context rot is real: even at 1M tokens, deeper context degrades reasoning.
- Overhead: CLAUDE.md, memory, and startup content consume tokens on every message (necessary but costs).

## Example

**Before optimization** (context pressure at 75%):
```bash
claude
> I need to fix the database transaction bug in user.ts, auth.ts, and session.ts. 
> Research how transactions work in our ORM and propose a fix.
```
Claude reads all three files (~8k tokens), searches for transaction patterns (~2k tokens), compiles a fix. On follow-up refinements, context pressure mounts.

**After optimization:**
```bash
# Session 1: delegate research
claude
> Use a subagent to research transaction handling in our ORM and current usage patterns.

# Subagent works in its own context; 6k tokens of file reads stay isolated. 
# You get a 500-token summary back.

> Now implement a transaction fix in user.ts based on that research.
# You read just user.ts (~2k tokens), implement, test.
```

Second approach uses less of *your* context window because research happened separately. You stay focused.

**With optimized CLAUDE.md:**
```markdown
# Project Setup
- ORM: SQLAlchemy with transaction context managers
- Tests: pytest in `tests/`, requires `TEST_DB_URL`
- Pattern: always use `with Session() as session:` for transaction safety
```

Claude remembers the pattern on every session; no need to re-read docs or search transaction examples. Saves ~1k tokens per session long-term.

## Notes & links

- **Token counting API:** use before sending expensive requests. `claude /context` estimates your session; the API estimates a single request.
- **Context awareness (beta):** Claude Sonnet 5, Sonnet 4.6, Sonnet 4.5, and Haiku 4.5 receive their remaining token budget in the system prompt. These models can plan ahead and avoid overshooting the limit.
- **Extended thinking and context:** thinking tokens count toward the window. On models that preserve thinking (Opus 4.5+), old thinking blocks accumulate; on earlier models, thinking blocks auto-strip to save space.
- **Prompt caching:** cached prefixes still occupy the context window—caching changes billing, not context capacity.
- **System prompt:** ~50 "instruction slots" occupied by Claude Code's system prompt; CLAUDE.md competes for the rest.
- **Large files:** a 10k-line source file can cost 5–10k tokens depending on content. Compress by being specific in prompts ("fix the bug in auth.ts" vs. "analyze auth.ts") so Claude reads only what's needed.
- **Hooks and output:** PostToolUse hooks fire after every tool event. Keep hook output concise (via `additionalContext` JSON) since it enters context without truncation.

**Related techniques:** [[claude-md-persistent-memory]], [[context-compaction-beta]], [[subagent-fan-out]], [[auto-memory-for-claude-code]]

**Official docs:**
- [Explore the context window (interactive timeline)](https://code.claude.com/docs/en/context-window) — shows every startup item and follow-up
- [Context windows (Claude API)](https://platform.claude.com/docs/en/build-with-claude/context-windows) — model sizes, overflow behavior, extended thinking
- [Compaction (beta)](https://platform.claude.com/docs/en/build-with-claude/compaction) — server-side summarization strategy
- [Best practices](https://code.claude.com/docs/en/best-practices) — context management as primary constraint
