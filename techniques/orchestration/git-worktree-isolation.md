---
id: git-worktree-isolation
title: Git worktree per-agent isolation for parallel development
category: orchestration
ecosystems: [claude-code, generic]
problem: Multiple agents on same branch collide on file writes; need per-agent isolated working directories.
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [agent-teams-coordination, supervisor-pattern, shared-context-file-handoff]
supersedes: []
sources:
  - {url: "https://www.augmentcode.com/guides/git-worktrees-parallel-ai-agent-execution", kind: blog, date: 2026-07-28}
  - {url: "https://www.mindstudio.ai/blog/parallel-agentic-development-git-worktrees", kind: blog, date: 2026-07-28}
  - {url: "https://zylos.ai/research/2026-02-22-git-worktree-parallel-ai-development/", kind: blog, date: 2026-07-28}
  - {url: "https://developer.upsun.com/posts/ai/git-worktrees-for-parallel-ai-coding-agents", kind: blog, date: 2026-07-28}
added: 2026-07-28
updated: 2026-07-30
---

## Problem

When multiple agents work on the same codebase:
- **Write conflicts:** Agent A saves a file, then Agent B overwrites it with different content. Agent A's changes are lost.
- **Read inconsistency:** Agent B reads a file while Agent A is modifying it, leading to partial or corrupted context.
- **Build contention:** Both agents trigger builds competing for the same output directories and ports.

Sequential `git checkout` is incompatible with parallelism (only one branch active). Cloning duplicates the entire `.git` object store, wasting disk space.

## How it works

Git worktrees let each agent have its own isolated working directory while sharing a single `.git` object store. Each agent:
1. Gets its own checked-out branch in a separate directory (`worktree-agent1/`, `worktree-agent2/`, etc.).
2. Operates on files without interfering with other agents.
3. Commits to the shared object store (no duplication).
4. Can merge or rebase independently.

```bash
# Main repo
git clone <repo> main-repo && cd main-repo

# Agent 1 gets isolated worktree on feature-1
git worktree add ../agent1-branch feature-1
cd ../agent1-branch
# Agent 1 edits files, commits

# Agent 2 gets isolated worktree on feature-2
git worktree add ../agent2-branch feature-2
cd ../agent2-branch
# Agent 2 edits files, commits independently

# Agents never collide on filesystem
```

## Setup

For Claude Code or any agent orchestrator:
1. Create a worktree per agent at startup.
2. Each agent gets its own `CWD` and git branch.
3. Agents commit to their branch independently.
4. Optionally merge/rebase at cleanup.

```bash
# Orchestrator setup
base_repo="/path/to/repo"
for agent in agent1 agent2 agent3; do
  git -C "$base_repo" worktree add \
    "../${agent}-work" \
    -b "work/${agent}-$(date +%s)"
done

# Each agent's environment
export CWD="/path/to/${agent}-work"
cd $CWD
# Agent works normally (git add, commit, etc.)

# Cleanup
git -C "$base_repo" worktree remove "../${agent}-work" --force
```

## When to use / when NOT

- **USE** when running 2+ agents in parallel on the same codebase.
- **USE** as the foundational isolation primitive for parallel development.
- **NOT** for sequential single-agent work (unnecessary overhead).

## Tradeoffs

- **Disk space:** Each worktree duplicates checked-out files (not the object store). For a 2GB repo, 4 worktrees = ~8GB checked-out, plus object store. Build artifacts multiply this further (monorepos can hit 50GB+ with 8 worktrees).
- **Setup overhead:** Creating/removing worktrees takes ~1-2 seconds per agent. Not significant for long-running tasks, but adds up if you spawn many agents.
- **Port/database conflicts:** Worktrees provide **filesystem isolation** only. If agents run dev servers or databases, they still collide on port 3000 or shared database state. Hybrid pattern (worktrees + per-agent containers) solves this but adds complexity.
- **Merge complexity:** Agents commit independently; merging back to main requires care to avoid conflicts. Upfront task decomposition (assign files per agent) reduces this.

## Example

Building an API with schema + endpoints + tests in parallel:
```bash
# Orchestrator creates worktrees
git worktree add ../schema-work -b work/schema
git worktree add ../api-work   -b work/api
git worktree add ../test-work  -b work/test

# Agent 1 (schema)
cd ../schema-work
# Designs and commits schema.sql, models.py
git commit -m "Add database schema"

# Agent 2 (api)
cd ../api-work
# Waits for schema commit, implements endpoints
git commit -m "Add REST endpoints"

# Agent 3 (test)
cd ../test-work
# Reads committed schema + API, writes integration tests
git commit -m "Add integration tests"

# Merge back
git -C "../main" merge work/schema
git -C "../main" merge work/api
git -C "../main" merge work/test
```

All three agents work in parallel without filesystem contention.

## Notes & links

Worktrees are lighter than clones but disk space compounds with many agents. Most teams cap at 4-10 concurrent worktrees before management overhead exceeds parallelism benefit.

Upfront task decomposition (assign which files each agent touches) is the main tool to avoid merge chaos.

Hybrid pattern: Pair worktrees with per-agent Docker containers to get both filesystem isolation and runtime isolation (ports, databases).

Tooling: Cursor 2.0 (Oct 2025) automates worktree management for up to 8 parallel agents. CodeRabbit provides bash-based worktree runner. See also Crystal (desktop app for parallel Claude sessions), plus `agentree`, `git-worktree-runner` (works with Claude/Cursor/Codex/Gemini), and `worktree-cli` (auto setup hooks + port isolation).

**Conflicts don't vanish — they move to merge time.** Parallel agents touching the same files guarantee integration pain. Use `git merge-tree` as a *pre-flight* check to detect conflicts between two worktrees *before* agents finish, so the orchestrator can redirect or serialize the conflicting work.

**Runtime isolation is separate from filesystem isolation.** Worktrees isolate files, not ports/DBs/deps. Override ports (`PORT=3001`), run `npm install` per worktree, and pair with database branching (e.g. Neon, PlanetScale) or per-agent Docker for full isolation.

This technique also sits in the `integration` space — it's the substrate for running multiple *different* agents (Claude, Codex, Cursor) on one repo, not just multiple Claude sub-agents.
