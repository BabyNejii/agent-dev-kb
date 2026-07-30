---
id: agent-teams-coordination
title: Agent Teams for parallel peer coordination
category: orchestration
ecosystems: [claude-code, claude-sdk]
problem: Subagents work in isolation with parent-child messaging only; need peer-to-peer coordination between agents on same codebase.
maturity: emerging
confidence: verified
effort_to_adopt: medium
works_with: [supervisor-pattern, git-worktree-isolation]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/agent-teams", kind: docs, date: 2026-07-28}
  - {url: "https://www.tembo.io/blog/claude-code-multi-agent-orchestration", kind: blog, date: 2026-07-28}
  - {url: "https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/guide/workflows/agent-teams.md", kind: github, date: 2026-07-28}
  - {url: "https://kargarisaac.medium.com/agent-teams-with-claude-code-and-claude-agent-sdk-e7de4e0cb03e", kind: blog, date: 2026-07-28}
added: 2026-07-28
updated: 2026-07-28
---

## Problem

Subagents run sequentially within a session and can only report results back to the parent. They cannot message each other, share discoveries mid-task, or coordinate without the main agent as an intermediary, which becomes a bottleneck when agents work on independent but related tasks.

## How it works

Agent Teams is an experimental feature in Claude Code that spins up multiple agents as a coordinated team. One session acts as the **team lead**, orchestrating work and assigning tasks. Teammates work independently in separate context windows (1M tokens each) and communicate directly via **peer-to-peer messaging** through a mailbox system, not only through the lead's synthesis.

Each agent has:
- Isolated 1M token context window
- Direct messaging to other teammates via SendMessage tool
- Access to shared task list and dependencies
- Independent file I/O on the shared codebase (via git worktrees or isolation layer)

## Setup

Enable Agent Teams via environment or settings.json:
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

In Claude Code or the SDK, create teammates and send messages:
```python
# Lead spawns teammates
team = create_team(lead_agent, [specialist_1, specialist_2, specialist_3])

# Teammate sends message directly to peer
SendMessage(to="specialist_2", message="Found bug in auth module, need design review")

# Tasks support dependencies
create_task(description="...", depends_on=[task_1_id], assigned_to="specialist_2")
```

## When to use / when NOT

- **USE** when multiple agents need to work on the same codebase in parallel with bidirectional communication.
- **USE** for complex projects where task dependencies and peer coordination are necessary.
- **NOT** for simple sequential work (subagents are lighter-weight).
- **NOT** for tasks that don't require agents to communicate mid-execution.

## Tradeoffs

- **Cost:** Each agent runs in its own context; coordination overhead multiplies tokens. Team of 4 agents ~4x the single-agent cost.
- **Latency:** Peer messaging adds coordination latency. Synchronous message waiting can serialize work.
- **Complexity:** Setting up task dependencies and mailbox logic is more complex than linear pipelines.
- **Benefit:** True parallelism on shared codebase with direct agent-to-agent coordination, not bottlenecked by lead synthesis.

## Example

Building a feature with API changes:
1. **Lead** receives spec, creates tasks: "Design schema", "Implement endpoints", "Write tests", "Update docs".
2. **Schema Agent** designs and commits database schema.
3. **API Agent** reads schema commit, implements endpoints, sends message: "Ready for tests".
4. **Test Agent** reads API code, writes integration tests, flags failures back to API Agent.
5. **Lead** synthesizes results and runs CI.

All four agents work in parallel with direct peer messaging.

## Notes & links

Agent Teams is experimental (as of Feb 2026 release). Enable via environment variable.
Combine with [[git-worktree-isolation]] for full filesystem isolation.
Peers with [[supervisor-pattern]] for hierarchical task delegation within a team.
