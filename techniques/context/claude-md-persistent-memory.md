---
id: claude-md-persistent-memory
title: CLAUDE.md files for persistent session memory
category: context
ecosystems: [claude-code]
problem: Each Claude Code session starts with empty context; repeating instructions, conventions, and project knowledge wastes tokens and causes Claude to re-learn the same patterns
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [auto-memory-for-claude-code]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/memory", kind: docs, date: "2026-07-28"}
  - {url: "https://medium.com/@bijit211987/the-complete-guide-to-claude-md-memory-rules-loading-and-cross-tool-compression-97cc12ed037b", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Claude Code sessions are stateless—each conversation begins with a fresh context window. Without persistent memory, developers repeat the same instructions (build commands, code style, architectural patterns) and Claude re-learns project conventions across sessions, burning context tokens on redundant information.

## How it works

CLAUDE.md files are markdown instructions you write and commit to a repository. Claude Code reads them at the start of every session in load order (user → project → local scope), injecting them as context. They're treated as instructions, not enforced configuration—Claude reads them and tries to follow them.

Load order proceeds from broadest (global user) to most specific (project root):
1. Managed policy CLAUDE.md (organization-wide)
2. User CLAUDE.md (`~/.claude/CLAUDE.md`)
3. Project CLAUDE.md (`./CLAUDE.md` or `./.claude/CLAUDE.md`)
4. Local CLAUDE.md (`./CLAUDE.local.md`, git-ignored)

## Setup

**Create a basic project CLAUDE.md:**
```markdown
# Project Overview
This is a TypeScript/React web app. Source in `src/`, tests in `test/`.

## Build & Test
- Run tests: `npm test`
- Format: `npm run format`
- Lint: `npm run lint`

## Code Style
- 2-space indentation, no tabs
- Use async/await, not callbacks
- Prefer const over let

## Architecture
- API handlers live in `src/api/`
- Components in `src/components/`
```

**Auto-generate with /init:**
```bash
claude /init
```
This scans your codebase and generates a starter CLAUDE.md with discovered commands and conventions.

**Organize large projects with `.claude/rules/`:**
Create `.claude/rules/` subdirectory with topic-specific files:
```
.claude/
├── CLAUDE.md           # Main instructions
└── rules/
    ├── testing.md      # Testing conventions
    ├── api-design.md   # API standards
    └── security.md     # Security guidelines
```

**Path-scoped rules (conditional loading):**
Add YAML frontmatter to load instructions only for matching files:
```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules
- All endpoints must validate input
- Return standard error format
```

**Keep files lean:**
Target <200 lines per file. Use path-scoped rules to load instructions only when Claude works with matching files. Import external files with `@path/to/file` syntax (expanded at load time).

## When to use / when NOT

**Use CLAUDE.md for:**
- Build and test commands developers will run
- Code style and formatting rules
- Project layout and module organization
- Common workflows and debugging techniques
- Architecture decisions and rationale

**Use auto memory (separate system) for:**
- Learned patterns Claude discovers during your session
- Debugging insights and workarounds
- Build output or test failures Claude should remember
- User preferences Claude observes

**NOT for:**
- Large reference docs (reference them with `@README` instead)
- Task-specific instructions (use skills or hooks)
- Temporary notes (use auto memory)
- Sensitive data (local `.CLAUDE.local.md` + .gitignore)

## Tradeoffs

**Strengths:**
- Persists across all sessions and team members (when committed)
- Shared via git, keeps team aligned
- Reduces context waste on repeated instructions
- Can be organized modularly with rules and imports
- Path-scoped rules load only relevant instructions

**Weaknesses:**
- Text lives in context window on every session (consumes tokens)
- Instructions are not enforced—Claude can ignore them
- Large files reduce adherence; files >200 lines hurt performance
- Conflicting instructions across files cause unpredictable behavior
- Changes require editing and committing; not as flexible as conversation

**Context budget:**
- Models can reliably follow ~150-200 instructions in context
- Claude Code's system prompt already occupies ~50 slots
- Aim for high-signal content only; trim what Claude can infer from code

## Example

Minimal but effective project CLAUDE.md:
```markdown
# Antigrav Agent KB

Backend: Python FastAPI, SQLAlchemy ORM. Tests in `tests/` with pytest.

## Build
- Setup: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Test: `pytest` (requires local Postgres)
- Dev server: `uvicorn main:app --reload`

## Code Style
- 4-space indentation; use Black for formatting
- Type hints on all functions
- API responses use standard error wrapper

## Architecture
- Routes in `app/routes/`, models in `app/models/`
- Database migrations in `migrations/`
- Always use context managers for DB sessions

## Gotchas
- Tests need `TEST_DB_URL` env var pointing to test Postgres
- Schema changes require migration; run `alembic upgrade head`
```

## Notes & links

- **Context optimization:** Run `/doctor` to trim a CLAUDE.md—it removes content Claude can derive from the codebase and keeps only pitfalls, rationale, and non-default conventions.
- **Large teams:** Organize with `.claude/rules/` and path-scoped rules. Exclude irrelevant CLAUDE.md from parent directories with `claudeMdExcludes` in `.claude/settings.local.json`.
- **Survival across compaction:** Project-root CLAUDE.md is re-read from disk after `/compact` and re-injected. Nested CLAUDE.md in subdirectories reload on-demand when Claude reads those files.
- **Structured imports:** Use `@path` to import external files (README, architecture docs). Imported files are expanded at load and don't reduce context.
- **Integration:** Pairs well with auto memory (Claude's learned notes) and hooks (enforcement at lifecycle events).

See also: [[auto-memory-for-claude-code]], [[claude-code-context-window]], [[path-scoped-rules]]
