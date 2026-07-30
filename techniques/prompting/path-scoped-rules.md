---
id: path-scoped-rules
title: Path-scoped rules for directory and file-type instructions
category: prompting
ecosystems: [claude-code]
problem: Large CLAUDE.md files consume tokens in every session; rules should load only when relevant to current work
maturity: established
confidence: verified
effort_to_adopt: low
works_with: [instruction-hierarchy-layering, claude-md-persistent-memory]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/memory#organize-rules-with-claude/rules/", kind: docs, date: "2026-07-28"}
  - {url: "https://code.claude.com/docs/en/memory#path-specific-rules", kind: docs, date: "2026-07-28"}
  - {url: "https://code.claude.com/docs/en/claude-directory", kind: docs, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Project instructions in CLAUDE.md load into every session, consuming tokens even when not relevant. Testing conventions shouldn't be in context during docs-only work; API rules shouldn't appear when editing frontend code. Large CLAUDE.md files reduce adherence and waste space better used for conversation history.

## How it works

Claude Code supports **path-scoped rules**: markdown files in `.claude/rules/` with optional `paths:` frontmatter that specify glob patterns. Rules without `paths:` load unconditionally at session start (like CLAUDE.md). Rules *with* `paths:` load lazily—only when Claude reads or works with files matching the patterns.

### Loading semantics

- **Unconditional rules** (no `paths:` field): Loaded at session start, included in every session like main CLAUDE.md.
- **Path-scoped rules** (with `paths:` field): Loaded on demand when Claude reads a file matching any glob in the `paths:` list. Once triggered, the rule persists in context for the session.
- **Subdirectory CLAUDE.md files**: Similar to path-scoped rules but based on directory boundaries. A `src/backend/CLAUDE.md` loads when Claude reads files under `src/backend/`. They concatenate with other CLAUDE.md files in the tree, not override them.

**Precedence**: All instruction files are concatenated into context rather than strictly overridden. Files higher in the directory tree appear first. When instructions conflict, Claude may choose arbitrarily; avoid duplication and contradictions rather than relying on override order.

## Setup

### Create path-scoped rules

Create a `.claude/rules/` directory in your project root. Each markdown file is a rule:

```text
your-project/
├── .claude/
│   ├── CLAUDE.md              # Main instructions (always loaded)
│   └── rules/
│       ├── testing.md         # Unconditional: loaded at startup
│       ├── api-design.md      # Path-scoped: loads when reading src/api/**
│       └── security/
│           └── secrets.md     # Subdirectories work; discovered recursively
```

### Unconditional rule (loaded always)

```markdown
# Testing Conventions

- Test files: co-located next to source, named `*.test.ts`
- Mocks: use descriptive factory functions, avoid mocking internals
- Coverage: 80% minimum for src/, 60% for tests/
```

### Path-scoped rule (loaded conditionally)

Add `paths:` frontmatter with glob patterns:

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "**/*.handler.ts"
---

# API Handlers

- All endpoints must validate input with Zod or similar
- Return shape: `{ data: T } | { error: string }`
- Log security events (auth failures, rate limits)
- Rate limit all public endpoints
```

When Claude reads `src/api/users.ts` or any `.handler.ts` file, this rule loads. It stays in context for the rest of the session.

### Monorepo: nested CLAUDE.md by team

For monorepos where teams have different conventions:

```text
monorepo/
├── CLAUDE.md                    # Shared conventions
├── packages/backend/
│   └── CLAUDE.md                # Backend team rules
├── packages/frontend/
│   └── CLAUDE.md                # Frontend team rules
└── .claude/rules/
    └── shared-testing.md        # Applies to all teams
```

Each `CLAUDE.md` loads when Claude works in that subdirectory. Use `claudeMdExcludes` in `.claude/settings.local.json` to skip teams' rules that aren't relevant:

```json
{
  "claudeMdExcludes": [
    "**/backend/CLAUDE.md"
  ]
}
```

## When to use / when NOT

**Use path-scoped rules when:**
- Rules apply to specific file types (`**/*.test.ts`, `**/*.sql`)
- Different rules apply in different directories (`src/api/` vs `src/web/`)
- Rules are large or specialized (don't clutter main CLAUDE.md)
- You want to keep context lean during sessions touching only some parts of the codebase

**Use unconditional rules when:**
- The instruction applies everywhere (code style, commit format)
- It's short enough to always be useful (< 20 lines)

**Use nested CLAUDE.md when:**
- Convention follows a directory/team boundary (monorepo teams)
- You need different build commands or architecture docs per subdirectory
- Teams should see only their own rules

**Don't use path-scoped rules for:**
- Task-specific instructions (use skills `/name` instead)
- One-time procedural guidance (use `/skill-name` or conversation)

## Tradeoffs

**Pro:**
- Rules load only when needed, reducing token waste
- No context clutter when working on unrelated code
- Clear file-type and directory boundaries
- Scales well in large projects

**Con:**
- A rule with `paths:` won't load in a fresh session if you immediately create a new file without reading existing ones in that directory first ("cold start" problem)
- More files to maintain; requires discipline not to duplicate rules
- Path matching is glob-based; complex patterns with brace expansion count against a budget (1000 expanded patterns per rule, 4 MiB limit)

## Example

**Scenario:** TypeScript + React frontend, Python + FastAPI backend, shared testing standards.

```text
project/
├── CLAUDE.md                    # Shared: Git workflow, naming conventions
├── .claude/
│   └── rules/
│       ├── testing.md           # Unconditional: test conventions (no paths:)
│       ├── frontend.md          # Path-scoped: src/web/**
│       └── api.md               # Path-scoped: src/api/**
```

**CLAUDE.md (shared):**
```markdown
# Project Conventions

## Commands
- Build: `npm run build`
- Test: `npm test`
- Format: `npm run format`

## Git Workflow
- Feature branches: `feature/issue-123`
- Commits: conventional format (feat: ..., fix: ...)
```

**.claude/rules/testing.md (unconditional):**
```markdown
# Testing Standards

- Test files next to source: `*.test.ts`, `*.test.tsx`
- Use Vitest; mock externals only
- Async tests: await and no dangling promises
```

**.claude/rules/frontend.md (path-scoped):**
```markdown
---
paths:
  - "src/web/**/*.tsx"
  - "src/web/**/*.ts"
---

# Frontend Rules

- Use React functional components only
- Design tokens for colors and spacing (no magic values)
- Accessible by default: WCAG AA, semantic HTML
- Mobile-first responsive design
```

**.claude/rules/api.md (path-scoped):**
```markdown
---
paths:
  - "src/api/**/*.py"
  - "**/*.handler.py"
---

# API Rules

- Use Pydantic for request validation
- Return shape: `{ "data": ..., "error": null }` or `{ "data": null, "error": "..." }`
- Log all authentication attempts
- Rate limit: 100 req/min for public endpoints
```

**Result:** When Claude edits `src/web/Button.tsx`, only `testing.md` and `frontend.md` load. When editing `src/api/users.py`, only `testing.md` and `api.md` load. Shared CLAUDE.md always present. No wasted context on inapplicable rules.

## Notes & links

- **Token efficiency:** Path-scoped rules are the main way to manage CLAUDE.md size in large projects. Split rules by file type or directory once CLAUDE.md approaches 200 lines.
- **Cold start caveat:** A path-scoped rule for `src/api/**` won't auto-load if you ask Claude to create `src/api/new-endpoint.ts` without first reading existing files in that directory. Work around this by having Claude read a reference file first, or make critical rules unconditional.
- **Combine with nested CLAUDE.md:** In monorepos, use nested CLAUDE.md for team/directory structure and `.claude/rules/` for cross-cutting concerns (testing, security, code style that applies everywhere).
- **See also:** [[instruction-hierarchy-layering]] covers the broader precedence model; [[claude-md-persistent-memory]] explains auto memory alongside manual CLAUDE.md files.

