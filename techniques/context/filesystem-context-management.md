---
id: filesystem-context-management
title: Filesystem as primary context layer for agents
category: context
ecosystems: [claude-code, claude-sdk, claude-api, generic]
problem: Putting all context in the prompt creates token overhead, makes just-in-time discovery difficult, and scatters state across sessions
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [shared-context-file-handoff, auto-memory-for-claude-code]
supersedes: []
sources:
  - {url: "https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", kind: github, date: 2026-07-30}
  - {url: "https://github.com/Meirtz/Awesome-Context-Engineering", kind: github, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

Sessions accumulate context that either bloats the prompt (tool outputs, build logs, test results, reference materials) or lives nowhere and must be re-discovered. Agents re-read the same files, recompute the same summaries, and forget outputs from earlier in the session. Large projects can't fit their full state in a single prompt, yet agents lose context between sessions because nothing persistent captures their working state.

## How it works

Use the filesystem as the primary context storage layer, not the prompt:
- **Tool output**: Write full results to `./outputs/<tool>.log` or `./<tool>-results.json` instead of echoing them into the conversation.
- **Plans and decisions**: Store in `./docs/plan.md`, `./docs/ADRs/`, or `./.context/` so they persist and can be consulted without re-prompting.
- **Agent state and scratchpads**: Use `./.context/scratchpad.md` or `./.agent-work/` for intermediate reasoning that doesn't belong in source code.
- **Discovery**: Agents discover needed context just-in-time via `ls`, `find`, or explicit file reads—avoiding upfront loading of everything.

The contract: the filesystem is **authoritative** for shared state. The prompt window references and excerpts from it, not the reverse.

## Setup

1. Define a context directory structure. Example:
   ```
   .context/
     ├── plan.md           # current task, next steps, completed tasks
     ├── findings.md       # research, debugging notes, discovered patterns
     ├── scratchpad.md     # ephemeral work, brainstorms, abandoned ideas
   docs/
     ├── ADRs/             # architecture decision records
     ├── api-surface.md    # API contracts the agent must respect
   outputs/
     ├── build.log         # last build output
     ├── test-results.json # last test run, machine-readable
     ├── coverage.json     # code coverage data
   ```

2. Write a discovery script or Claude Code hook that agents can call:
   ```bash
   find .context -name "*.md" -type f | head -20
   find outputs -name "*.json" -type f
   ```

3. Train agents (via CLAUDE.md or task instructions) to:
   - Write to `.context/plan.md` when creating/updating plans (don't describe the plan in chat).
   - Write large outputs to files and reference them: "I logged results to `outputs/test-results.json`; here's a summary: ..."
   - Start new sessions by reading `.context/plan.md` and `docs/ADRs/` to restore context.

## When to use / when NOT

**Use when:**
- Managing large projects (50+ files, 500K+ lines of code) where full context won't fit.
- Multiple agents need shared discoverable state (without explicit handoff files).
- Sessions are long-running; output accumulates faster than you can read it into context.
- You need persistent agent working state across sessions.

**Don't use when:**
- Context is small enough to fit comfortably (< 10K relevant tokens).
- Real-time latency is critical (filesystem I/O adds overhead).
- Agents run in isolated sandboxes without filesystem access.
- Concurrent agents write to overlapping files (requires locking/merging discipline).

## Tradeoffs

| Benefit | Cost |
|---------|------|
| Reduces prompt bloat; frees tokens for reasoning | More I/O; adds 100-500ms per discovery/read |
| Persistent across sessions without session memory | Filesystem state can drift; requires explicit cleanup |
| Agents discover context on-demand | Need a clear directory structure; must train agents to use it |
| Separates concerns (outputs, plans, source) | Harder to coordinate concurrent agents on same files |

## Example

Agent flow with filesystem context:
```
1. Agent starts; reads .context/plan.md
   → "Current task: refactor Auth module. Status: in-progress. Next: write tests."

2. Agent explores codebase, generates test file
   → Writes results to: outputs/proposed-tests.md

3. Agent runs tests
   → Writes results to: outputs/test-run-<timestamp>.json
   → References in chat: "Tests: 120 pass, 3 fail. Details in outputs/test-run-<ts>.json"

4. Agent encounters blocker
   → Writes to .context/scratchpad.md: "Blocked on: circular import in auth/provider.ts"
   → References in chat: "Logged blocker to .context/scratchpad.md"

5. Next session starts; agent reads .context/ to resume
   → No re-prompting of prior work; context restored from files
```

## Notes & links

- Distinct from [[shared-context-file-handoff]]: that technique uses a single HANDOFF.md for agent-to-agent state passing. This approach uses the filesystem as the *primary* context layer for all agents.
- Relates to [[auto-memory-for-claude-code]] — both persist state across sessions, but filesystem is more explicit/discoverable; auto-memory is more implicit/automatic.
- Requires discipline: filesystem state must be kept in sync with reality. Use git tracking or append-only logs (JSONL) for auditability.
- For concurrent agents: add file locks, versioning, or a coordination layer (e.g., MCP server) to prevent write conflicts.
