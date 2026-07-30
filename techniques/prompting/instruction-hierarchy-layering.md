---
id: instruction-hierarchy-layering
title: Instruction hierarchy across CLAUDE.md, system prompt, and skills
category: prompting
ecosystems: [claude-code, claude-sdk]
problem: Conflicting or scattered instructions cause agent behavior inconsistency
maturity: established
confidence: reported
effort_to_adopt: medium
works_with: [prompt-caching-with-claude-api]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices", kind: docs, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Instructions scattered across system prompt, CLAUDE.md, skills, and inline comments conflict, become outdated, or grow too large to manage. Developers don't know where to put rules (persistent vs session-specific) or which layer takes precedence.

## How it works

Claude Code / SDK support layered instruction models. While the effective precedence depends on implementation details, the general pattern is:

1. **User's direct request** (highest priority in conversation) — can override session-level rules
2. **CLAUDE.md / project instructions** — persistent, loaded each session; takes precedence over user-level files due to load ordering
3. **System prompt** (SDK) — customizable per request
4. **Skills** (Claude Code) — capability discovery
5. **Default behavior** (lowest) — model defaults

Within CLAUDE.md, different scopes are loaded: user (`~/.claude/CLAUDE.md`), project (`.claude/CLAUDE.md` or root), and directory-specific. More specific scopes (project over user) generally take precedence. However, note that Anthropic's documentation indicates files are **concatenated** rather than strictly overridden, so conflicting instructions should be avoided rather than relied upon to supersede.

Claude Code also supports `.claude/rules/` directories with glob-scoped rules (e.g., rules applying only to test files or API routes).

## Setup

### Layer 1: Persistent project instructions (CLAUDE.md)

**File location:** `CLAUDE.md` in repo root or `.claude/CLAUDE.md`

```markdown
# Project Guidelines

## Role
You are a backend engineer on the payments team.

## Core Rules
- Always read the file before editing
- Validate input at system boundaries, not in helpers
- Never use force-push on shared branches
- Run tests before committing

## Context
- Payment processing uses Stripe API
- Database migrations require review
- Customers in US, UK, EU only

## Tool Priority
Use specialized tools over bash:
- Read instead of cat
- Edit instead of sed
- Grep instead of grep/rg
```

**Best for:** Rules applying across all sessions (safety, domain context, coding standards).

### Layer 2: System prompt customization (SDK)

```python
# In agent definition
client.messages.create(
    model="claude-opus-5",
    system=[
        # Default system prompt (if using preset="claude_code")
        # Your append:
        {
            "type": "text",
            "text": """
Additional context for this specific task:
- Focus on security audits for this run
- Report findings in JSON format
- Flag any hardcoded credentials
            """
        }
    ],
    messages=[...]
)
```

**Best for:** Session-specific guidance that varies by request (different for code review vs feature dev).

### Layer 3: Scoped rules (Claude Code .claude/rules/)

**File location:** `.claude/rules/security.md` with glob patterns

```markdown
# Security Rules

Applies to: src/auth/**, src/api/**

- Validate all JWT tokens
- Never log passwords or tokens
- Use secure random for session IDs
- Encrypt sensitive fields at rest
```

**Best for:** Domain-specific rules (different rules for tests, auth, payment processing).

### Layer 4: Skills

**File location:** `.claude/skills/` or `SKILL.md` files

```yaml
name: code-review
trigger: "code review"
description: Review pull request for bugs and style issues
```

**Best for:** Reusable capabilities discoverable on-demand.

## When to use / when NOT

**CLAUDE.md:**
- Rules applying to every session
- Coding standards
- Safety constraints
- Project context
- Don't change per-task

**System prompt append:**
- Session-specific task framing
- Changes per request (different effort level, different success criteria)
- Output format for this run
- Temporary guidance

**Scoped rules (.claude/rules/):**
- File-type or directory-specific rules
- Different rules for tests vs production code
- Rules that shouldn't clutter main CLAUDE.md

**Skills:**
- Optional, on-demand capabilities
- Workflows invoked by user
- Discovery-based (model chooses if available)

## Tradeoffs

- **Pro:** Clear precedence; user can always override
- **Pro:** Persistent rules don't repeat on every request
- **Con:** Requires discipline (where does each rule live?)
- **Con:** Rule changes need to be tested (misconfiguration affects all sessions)
- **Con:** Large CLAUDE.md consumes tokens; move to skills if optional

## Example

**Scenario:** Backend + frontend team with shared conventions, but different rules per context.

**CLAUDE.md (repo root):**
```
- Both teams: Always read files before editing, never force-push
- Both teams: Test before commit
- Backend: Use prepared statements for DB queries
- Frontend: Use design system components
```

**.claude/rules/backend.md** (glob: `src/backend/**`):
```
- Validate input at API boundaries
- Log security events
- Database migrations require peer review
```

**.claude/rules/frontend.md** (glob: `src/frontend/**`):
```
- Use design tokens for colors/spacing
- Accessible by default (WCAG AA minimum)
- Mobile-first responsive design
```

**Request-time system prompt (for code review run):**
```
This is a security-focused code review.
Flag: hardcoded credentials, weak crypto, unvalidated input.
Output format: JSON with severity levels.
```

Result: Shared context, role-specific rules, task-specific framing—all clear.

## Notes & links

- **Token efficiency:** Move large, stable rules to CLAUDE.md (loaded at session start), keep dynamic guidance in request-time system prompt. Works well with [[prompt-caching-with-claude-api]].
- **Testing rules:** Changes to CLAUDE.md affect all future sessions; test locally first (`claude /test`).
- **Avoid conflicts:** Since files are concatenated rather than strictly overridden, contradictory instructions between layers cause confusion. Better to avoid conflicts than rely on override precedence.
- **Simplicity:** Start with just CLAUDE.md. Add scoped rules only if different rules need different contexts (e.g., test vs production code).
