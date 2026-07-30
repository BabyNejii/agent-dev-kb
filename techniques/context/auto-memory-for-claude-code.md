---
id: auto-memory-for-claude-code
title: Auto memory for persistent learning across Claude Code sessions
category: context
ecosystems: [claude-code]
problem: Claude forgets learnings across sessions (build commands, debugging patterns, test quirks); repeated discoveries waste tokens and time
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [claude-md-persistent-memory]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/memory", kind: docs, date: "2026-07-28"}
  - {url: "https://medium.com/@porter.nicholas/teaching-claude-to-remember-part-2-remember-everything-memory-system-1b496d1f0022", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Without memory, Claude rediscovers the same patterns in every session. You tell Claude "the tests require local Redis," Claude forgets it, you tell it again. Claude learns your build command in session 1, learns it again in session 2. Each rediscovery burns context tokens and slows you down.

## How it works

Auto memory lets Claude write notes for itself based on your corrections and the patterns it observes. When Claude discovers something useful—a build command, a test quirk, a debugging insight—it saves it to machine-local memory files. The first 200 lines (or 25KB) of `MEMORY.md` load at session start, giving Claude context for the next session.

Auto memory is **machine-local** (not shared across developers) and **per-repository** (all worktrees and subdirectories share one memory). Claude decides what's worth saving based on whether it would help in future conversations.

## Setup

Auto memory is **on by default.** No setup required. Claude saves notes as it works.

**View and edit memory:**
```bash
claude /memory
```
Select a file to open in your editor. Everything is plain markdown you can read, edit, or delete.

**Enable/disable:**
```bash
# Toggle in UI with /memory, or set in ~/.claude/settings.json:
{"autoMemoryEnabled": false}

# Or per-project in .claude/settings.json:
{"autoMemoryEnabled": false}
```

**Custom storage location:**
```json
{
  "autoMemoryDirectory": "~/my-custom-memory-dir"
}
```

**Storage structure:**
```
~/.claude/projects/<project>/memory/
├── MEMORY.md           # Index (~200 lines, loaded at start)
├── debugging.md        # Detailed debugging patterns
├── api-conventions.md  # API design decisions
└── build-info.md       # Build/test commands and quirks
```

## When to use / when NOT

**Auto memory is best for:**
- Build commands and test setup (first run, then Claude recalls)
- Debugging patterns and workarounds Claude discovers
- Project conventions Claude infers from code
- Test failures and how to fix them
- Environment setup quirks (Redis required, specific Node version, etc.)

**Use CLAUDE.md instead for:**
- Explicit instructions that must always be followed
- Code style rules and architecture decisions
- Company policies or security requirements
- Information shared across the team (checked in to git)

**Why split them:**
- CLAUDE.md: what you mandate; auto memory: what Claude observes
- CLAUDE.md: team knowledge in git; auto memory: your machine's learnings
- CLAUDE.md: persists but requires editing; auto memory: hands-free

## Tradeoffs

**Strengths:**
- Automatic—no manual effort to maintain
- Machine-local—no privacy concerns about shared discoveries
- Hands-off learning—Claude saves what it judges important
- Reduces re-discovery of build commands, quirks, patterns

**Weaknesses:**
- First 200 lines only load at startup (rest on-demand)
- Machine-local—not shared with team
- Bloat over time—outdated learnings accumulate
- Competing with CLAUDE.md for context attention

**Context budget:**
Only `MEMORY.md` loads at startup (~200 lines / 25KB limit). Topic files are loaded on-demand when Claude reads them. This is tighter than CLAUDE.md, so keep it lean.

## Example

Typical auto memory after a few sessions on a Node.js project:

**MEMORY.md (index, loaded at startup):**
```markdown
- Build: `npm install && npm run build`
- Test: `npm test` (requires `TEST_DB=postgres://localhost/test`)
- Common test issue: "Cannot find module X" → run `npm install` first
- API server: `npm run dev` on port 3000, check `/health` for readiness
- Postgres migrations: `npm run migrate` before tests
```

**debugging.md (loaded on-demand):**
```markdown
## Port 3000 already in use

If `npm run dev` fails with "EADDRINUSE", find the process:
```bash
lsof -i :3000 | grep node
kill -9 <pid>
```

Then restart.

## TypeScript type errors in build

Tests pass but build fails? Check tsconfig.json. The project has `skipLibCheck: true` 
but the build uses `skipLibCheck: false`. Make them consistent.
```

**api-conventions.md:**
```markdown
All API responses wrap errors:
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "User-facing message",
    "details": {...}
  }
}

Status codes: 200 (OK), 400 (client error), 500 (server error).
```

## Notes & links

- **Truncation:** If `MEMORY.md` exceeds 200 lines/25KB, Claude is reminded to shorten it. Keep one line per entry, move details to topic files, merge or drop stale entries.
- **Editing:** You can (and should) clean up memory periodically. Outdated learnings clutter context.
- **Subagent memory:** Subagents can maintain their own separate auto memory. See subagent config.
- **Comparison with CLAUDE.md:** CLAUDE.md is what you write; auto memory is what Claude learns. Both load at startup but CLAUDE.md loads in full, auto memory is capped at 200 lines.
- **Interaction:** Combine with CLAUDE.md: CLAUDE.md for team-wide rules, auto memory for your learnings on this machine.

See also: [[claude-md-persistent-memory]], [[claude-code-context-window]]
