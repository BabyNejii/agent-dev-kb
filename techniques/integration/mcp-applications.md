---
id: mcp-applications
title: MCP Applications for structured agent task automation
category: integration
ecosystems: [mcp]
problem: Simple tool calls don't capture rich agent workflows; MCP Apps provides semantics for multi-step tasks, async execution, and agent communication
maturity: experimental
confidence: reported
effort_to_adopt: high
works_with: [mcp-as-integration-layer]
supersedes: []
sources:
  - {url: "https://toloka.ai/blog/the-future-of-mcp-enterprise-adoption/", kind: blog, date: "2026-07-28"}
  - {url: "https://www.workos.com/blog/everything-your-team-needs-to-know-about-mcp-in-2026/", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

MCP servers expose tools as individual function calls (e.g., "create a GitHub PR", "query Jira"). But real agent workflows are richer: multi-step orchestrations, asynchronous long-running tasks, inter-agent communication, and rich structured outputs. Plain tools can't express these; agents have to infer structure from untyped text.

## How it works

MCP Applications (launched January 2026) extend MCP beyond single tool calls to include:

- **Tasks**: Multi-step workflows with explicit steps, dependencies, and completion signals
- **Elicitations**: Structured schemas for agent-to-human clarification (instead of freeform text)
- **Async handling**: Launch work in one request, retrieve results later (critical for non-blocking workflows)
- **Multi-agent patterns**: Agents can queue work for other agents and retrieve results asynchronously
- **Structured output**: Rich semantics instead of raw tool responses

Example: An MCP Application for "code review" might define:
- Task with steps: (1) fetch PR, (2) analyze code, (3) generate suggestions, (4) post review
- Elicitation schema: "Request clarification on which areas to focus"
- Output schema: structured suggestions with severity, location, and remediation

## Setup

As of July 2026, MCP Apps are still in active development and tooling is limited. General approach:

1. Define an MCP App schema that extends basic MCP tool definitions with task, elicitation, and async semantics
2. Implement the server to handle task dispatch, polling, and structured output
3. Register the app with a client (Claude Code, Anthropic API) that supports MCP Apps
4. Agents call the app with task definitions instead of raw tool calls

**Note:** Official SDKs and documentation are still stabilizing; expect APIs to change.

## When to use / when NOT

- **USE** when you need multi-step agent workflows with explicit checkpoints (e.g., "run tests, wait for results, decide on next step")
- **USE** for long-running background tasks that shouldn't block the agent
- **USE** for agent-to-agent handoff (one agent queues work for another)
- **NOT** for simple, synchronous tool calls (plain MCP servers are simpler)
- **NOT** if all your work is human-initiated (extra complexity for no gain)

## Tradeoffs

**Maturity:** MCP Apps launched in January 2026 and are not yet widely adopted. Tooling and SDKs are still stabilizing.

**Complexity:** Rich semantics mean richer server code. A task-based app requires explicit state management, polling logic, and structured schemas.

**Compatibility:** Not all MCP clients support Apps yet. Check your agent's docs before investing.

## Example

**Plain MCP (tools only):**
```
Agent: "Run tests in test-suite-A"
→ Tool call: execute_tests(suite=A)
→ Agent waits for response (blocks)
→ Tool hangs on 500-second test run
→ Agent times out
```

**MCP Application (tasks + async):**
```
Agent: "Run tests in test-suite-A and report"
→ App call: start_task(type=test_run, suite=A)
→ App returns: {task_id: abc123, status: queued}
→ Agent continues other work
→ Later: Agent polls or receives callback: {task_id: abc123, status: complete, results: […]}
→ Agent acts on results
```

## Notes & links

- MCP Apps were the first official extension to the MCP spec, announced at Anthropic's January 2026 roadmap update
- 2026 roadmap also includes: stateless HTTP transport, server discovery protocols, governance maturation (contributor ladder), and enterprise features (OAuth 2.1, audit trails)
- Related: [[mcp-as-integration-layer]] (foundational tool protocol)
