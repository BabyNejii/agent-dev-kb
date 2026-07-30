---
id: shared-context-file-handoff
title: Shared context file (HANDOFF.md) for agent state passing
category: integration
ecosystems: [claude-code, generic]
problem: Sequential agents lack shared state; context is lost or re-explained on each session
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [git-worktree-isolation, claude-antigravity-handoff]
supersedes: []
sources:
  - {url: "https://github.com/gsailing19/agent-handoff/tree/main/", kind: github, date: "2026-07-28"}
  - {url: "https://ddunford.medium.com/passing-information-between-claude-code-agents-the-right-way-9ad91998690e", kind: blog, date: "2026-07-28"}
  - {url: "https://fazm.ai/blog/claude-code-architecture-handoff-pattern", kind: blog, date: "2026-07-28"}
  - {url: "https://www.mejba.me/blog/handoff-skill-claude-code-multi-session", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

When sequential agents or multi-session workflows run on the same project, context is lost:
- Agent A completes analysis, exits
- Agent B starts fresh with no knowledge of A's decisions
- B re-explores the same ground or makes conflicting choices
- No audit trail of decisions or dependencies

Passing context via shared memory doesn't work: agents can't see each other's memory. Pasting between sessions loses structure and causes context bloat.

## How it works

Use a dedicated **handoff file** (typically `HANDOFF.md` or `.claude/context-transfer/` files) as the interchange format. Each agent reads it on start, writes updates on finish.

**Structure (Markdown format, most portable):**
```markdown
# Handoff Context

## Summary
[What was accomplished in this session]

## Key Decisions
- [Decision 1] — why
- [Decision 2] — why

## Traps & Failed Approaches
- [Approach that failed] — why it failed
- [Common mistake] — how to avoid it

## Working Agreements
- Test before commit
- Use kebab-case for branch names
- Notify before major refactors

## Pending Work
- [ ] Implement LoginForm component
- [ ] Add test coverage for auth module
- [ ] Review PR feedback

## Relevant Files & Changes
- `src/auth.ts` (lines 1–50): Core auth logic, changed twice
- `src/components/LoginForm.tsx` (NEW): Form component, needs tests
- `.env.example`: Updated with new secrets

## Next Steps for Next Agent
1. Review Traps section
2. Focus on: test coverage for auth module
3. Then pick up: implement LoginForm component

---
Updated: 2026-07-28 | Agent: Investigator | Session: abc123
```

**Alternative (YAML, for stricter pipelines):**
```yaml
version: 1
agent: Investigator
timestamp: 2026-07-28T10:00:00Z
summary: "Analyzed auth module, found 3 gaps"
decisions:
  - decision_id: use-jwt
    description: "Use JWT for session tokens"
    rationale: "Stateless, scales horizontally"
  - decision_id: require-2fa
    description: "Require 2FA for admin accounts"
    rationale: "Security requirement from ENG-4521"
completed:
  - implement-jwt-middleware
failed:
  - name: "Redis session store"
    reason: "Too much operational overhead; JWT simpler"
pending:
  - task_id: test-2fa
    description: "Add tests for 2FA flow"
    priority: 1
next_agent_focus:
  - "Review decisions section first"
  - "Implement tests for 2FA"
files_changed:
  - path: "src/middleware/jwt.ts"
    lines: "1-60"
    change: "NEW"
```

## Setup

### Using a skill (Claude Code):
Many teams implement a `/transfer-context` skill that writes the handoff automatically:
```bash
/transfer-context
```

The skill:
1. Gathers session context (what was done, decisions, traps)
2. Writes to `.claude/context-transfers/<random-8-chars>.md`
3. Outputs only a path (not the full content)
4. Next session copy-pastes the path at the start

### Manual setup:
1. Create `HANDOFF.md` in project root (or `.claude/handoff.md` for private)
2. Each agent appends a section with date, decisions, and pending work
3. Next session reads it first

### For cross-tool portability:
Markdown handoff is portable across Claude Code, Cursor, Copilot CLI, Gemini CLI, and any text-reading agent. Some teams move work between three agent tools using the same Markdown file — no format conversion needed.

## When to use / when NOT

- **USE** for sequential agents (one finishes, next starts)
- **USE** for human-in-the-loop workflows (agent → human review → next agent)
- **USE** for cross-tool handoffs (one tool can't complete, next tool picks up)
- **NOT** for single-session work (overhead for no gain)
- **NOT** if agents have full shared memory (e.g., real database with agent event log)

## Tradeoffs

**Markdown vs. YAML:**
- Markdown: Human-readable, portable, fuzzy (no schema validation)
- YAML: Strict schema, validated, less portable across tools

Start with Markdown for portability. Graduate to YAML if validation matters (e.g., pipeline workflows with many agents).

**Freshness:** Handoff files only capture what was written. Partial or missed updates break the handoff. Automate writing (via skill or hook) to avoid stale files.

**Context loss:** An agent might miss details not in the handoff. This is actually a feature—forces clear, communicable decisions—but it means the handoff must be thorough.

## Example

**Session A (Investigator):**
```markdown
# Handoff: Auth Module Investigation

## Summary
Analyzed auth module. Found 3 gaps: no 2FA, JWT expiry not enforced, no rate limiting.

## Key Decisions
- Use JWT for stateless tokens (scales better than Redis)
- 2FA required for admins only (security requirement from ENG-4521)
- Use bcrypt for password hashing (already in dependencies)

## Traps
- Don't use `jsonwebtoken@7.x` — has vulns; need 9.x+
- Rate limiting on login endpoint is critical; skip it and bots will hammer

## Pending
- [ ] Implement JWT middleware
- [ ] Add 2FA flow for admin accounts
- [ ] Write tests for both

## Next Steps
Implement JWT middleware first (quickest win); then 2FA.

---
Updated: 2026-07-28 | Agent: Investigator
```

**Session B (Builder), reads handoff first:**
```
User: "Continue from last session"
→ Agent reads HANDOFF.md
→ Agent notes: JWT decision already made, don't re-debate
→ Agent checks traps: jsonwebtoken@7.x = bad, use 9.x
→ Agent starts: "I see you decided JWT. I'll implement the middleware."
→ Agent writes tests immediately (as per Traps section)
```

**Result:** No re-exploration, no conflicting decisions, faster progress.

## Notes & links

- **File-based handoff protocol**: Open source at [gsailing19/agent-handoff](https://github.com/gsailing19/agent-handoff) — routes agent outputs through filesystem to bypass context compression (~80% info loss in shared memory)
- **Portability insight:** Markdown handoff is a key enabler for cross-tool agent workflows. Some practitioners move work between Claude Code, Cursor, and Codex CLI using the same file.
- **Best practice:** Pair with [[git-worktree-isolation]] for full workflow isolation (file isolation + state isolation)
- Related: [[claude-antigravity-handoff]] (tool-to-tool handoff)
