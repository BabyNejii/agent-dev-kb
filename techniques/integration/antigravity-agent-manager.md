---
id: antigravity-agent-manager
title: Antigravity Agent Manager for multi-agent orchestration
category: integration
ecosystems: [antigravity]
problem: Running multiple agents in parallel requires manual coordination; no unified view of progress or async task delegation
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [mcp-as-integration-layer, shared-context-file-handoff]
supersedes: []
sources:
  - {url: "https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/", kind: docs, date: "2026-07-28"}
  - {url: "https://codelabs.developers.google.com/getting-started-google-antigravity", kind: docs, date: "2026-07-28"}
  - {url: "https://antigravity.google/blog/google-io-2026", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Running multiple agents on a development task requires:
- **Orchestration**: Which agent runs next? On what?
- **Background work**: Long-running tasks block the UI; you can't see progress
- **Verification**: Did agent 1's output meet the spec? Human review cycle needed
- **Progress tracking**: Where are all agents at? What's pending?

Antigravity's Agent Manager (v2.0, May 2026) provides a unified orchestration surface for spawning, monitoring, and directing multiple agents in parallel.

## How it works

**Core capabilities:**

1. **Agent spawning**: Create multiple agents targeting different tasks from a single UI
   - Each agent runs asynchronously; you see live progress
   - Agents can share context/state through shared files or MCP servers

2. **Parallel execution**: Multiple agents work on the same codebase simultaneously
   - Under the hood uses git worktrees for isolation (no file conflicts)
   - Each agent has its own branch and working directory

3. **Artifact-based verification**: Instead of reviewing logs, agents produce tangible deliverables
   - Task lists, plans, screenshots, browser recordings
   - Leave inline feedback; agents incorporate it without stopping execution

4. **Knowledge persistence**: Store learnings and code snippets for future tasks
   - Agents access a shared knowledge base (improves on future tasks)

5. **Scheduled tasks**: Agents can run on cron schedules with pre-specified tasks
   - E.g., "Every night at 2am, run dependency audits"

**Architecture:**
```
Antigravity UI (Agent Manager)
├── Agent A (feature-impl) → worktree-A/ → git branch: feature-x
├── Agent B (feature-test) → worktree-B/ → git branch: feature-tests-x
└── Agent C (docs)         → worktree-C/ → git branch: docs-update-x
     ↓ (all agents can access)
   Shared context file (HANDOFF.md, config, etc.)
   MCP servers (GitHub, Jira, monitoring)
```

## Setup

### Installation:
Download Antigravity 2.0 (desktop app, May 2026+) from https://antigravity.google

### Create a multi-agent workflow:

1. **Open project** in Antigravity
2. **Create agents**:
   - Agent A: "Implement LoginForm component"
   - Agent B: "Write tests for LoginForm"
   - Agent C: "Update docs"
3. **Set dependencies** (optional): Agent B waits for Agent A to complete
4. **Monitor**: Agent Manager shows all progress live
5. **Provide feedback**: Review artifacts (screenshots, PRs, test results); edit feedback inline
6. **Merge**: Once all agents finish, merge their branches sequentially

### Wire up shared context (optional):
```bash
# Create shared handoff file
echo "# Handoff" > HANDOFF.md

# All agents read/write HANDOFF.md; Agent Manager orchestrates sequencing
```

## When to use / when NOT

- **USE** when parallelizing independent feature work (e.g., UI components, tests, docs)
- **USE** for background maintenance tasks (nightly dependency audits)
- **USE** for human-in-the-loop: agent → artifact → human feedback → agent continues
- **NOT** if agents must work on overlapping code (merge conflicts; use dependency ordering instead)
- **NOT** if you need fine-grained control (prefer Claude Code or Antigravity CLI for hands-on work)

## Tradeoffs

**Coordination complexity:** The more agents you spawn, the more coordination needed at merge time. Conflicts don't disappear; they move to merge time. Plan work boundaries carefully.

**Maturity:** Antigravity 2.0 launched May 2026. Agent Manager is relatively new; tooling and best practices are still emerging. Expect UX improvements and API changes.

**Vendor lock-in:** Antigravity is Google-owned. Multi-agent workflows are partially captured in Antigravity's proprietary format (agent configs, knowledge base). Exporting to other platforms is limited.

**Context limits:** Each agent operates independently. Shared context (HANDOFF.md, MCP servers) helps, but agents can still make conflicting decisions. Requires careful design.

## Example

**Sequential work (traditional):**
```
You: "Implement LoginForm"
→ Wait for you to finish
→ You: "Write tests"
→ Wait for you to finish
→ You: "Update docs"
→ Total time: 3 hours
```

**Parallel work (Antigravity Agent Manager):**
```
You: "Spawn 3 agents"
→ Agent A: Implement LoginForm (working)
→ Agent B: Write tests (waiting for A's artifacts)
→ Agent C: Update docs (started immediately)
→ Agent A finishes → Agent B unblocks
→ Total time: ~1.5 hours (parallelism gain: 50%)
```

## Notes & links

- **Scheduled tasks**: New in Antigravity 2.0 (May 2026); define cron schedules for recurring agent work
- **Knowledge base**: Treats learning as a core primitive; agents store and reuse context across tasks
- **Integration**: Antigravity CLI shares the same agent harness as Antigravity Desktop; improvements to core agents auto-apply everywhere
- **Multi-workspace support**: Manage multiple projects/repos via Antigravity Projects feature
- Related: [[claude-antigravity-handoff]] (Claude Code ↔ Antigravity handoff pattern), [[git-worktree-isolation]] (underlying isolation mechanism)
