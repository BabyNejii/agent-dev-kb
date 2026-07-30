---
id: mcp-as-integration-layer
title: MCP as the universal integration layer for agent tooling
category: integration
ecosystems: [claude-code, claude-sdk, claude-api, mcp]
problem: Every agent needs custom integrations to each tool; MCP standardizes how agents talk to external systems
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [mcp-applications]
supersedes: []
sources:
  - {url: "https://modelcontextprotocol.io/introduction", kind: docs, date: "2026-07-28"}
  - {url: "https://code.claude.com/docs/en/mcp", kind: docs, date: "2026-07-28"}
  - {url: "https://www.anthropic.com/news/model-context-protocol", kind: docs, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Before MCP, every AI platform (Claude Code, Cursor, Copilot) had to build custom integrations for every external tool (Jira, Slack, GitHub, PostgreSQL). This created fragmentation: a tool integrated with Claude Code didn't work with Copilot, forcing teams to rebuild connectors. Agents couldn't leverage the full tool ecosystem.

## How it works

MCP is a vendor-neutral protocol that decouples tool capability from agent identity. A single MCP server implementation (e.g., a GitHub MCP server) works identically whether called by Claude Code, Cursor, or any other MCP-compatible agent.

**Architecture:**
- **MCP Client** (e.g., Claude Code) sends requests
- **MCP Server** (e.g., GitHub MCP server) handles the request and interacts with the external tool
- **External Tool** (e.g., GitHub API) is accessed by the server

**Transport options:**
- **stdio** (local): Run server as a subprocess, ideal for local databases or file tools. No network overhead. Downside: no automatic reconnect on crash.
- **HTTP** (remote): Connect to cloud-hosted servers. Includes automatic reconnect retry for transient failures.

## Setup

### For Claude Code:

1. Find an existing MCP server or [check the official registry](https://github.com/modelcontextprotocol/servers)
2. Register it with: `claude mcp add <name> <executable-or-url>`
3. Verify in tool list; start a new session
4. Claude can now call that tool directly in prompts

Example: `claude mcp add github https://github-mcp.example.com`

### To expose Claude Code as a server:
Run `claude mcp serve` to expose Claude Code's tools (file editing, bash, search) to other MCP clients like Claude Desktop or Cursor.

## When to use / when NOT

- **USE** when you find yourself copying data from external tools into chat (Jira tickets, monitoring dashboards, database results)
- **USE** to share tool integrations across teams (one server, many agents)
- **NOT** if you only work with one agent and one tool (overkill)
- **NOT** if the tool has a ready, direct Claude integration (no extra abstraction needed)

## Tradeoffs

**Token budget:** Each connected server adds tool schemas to Claude's context on every turn. Start with 1–2 servers targeting your most common tasks; 20+ servers create noticeable overhead.

**Security:** MCP servers that fetch external content can expose you to prompt injection. Verify you trust each server before connecting.

**Discovery:** No central registry with quality signals. Check [Anthropic's reference repo](https://github.com/modelcontextprotocol/servers) or the [Anthropic Directory](https://www.anthropic.com/docs/build-with-claude/agents/integration/mcp-servers) before building custom.

## Example

**Without MCP:**
```
User: "Find the user with email in ticket ENG-4521"
→ User copies Jira ticket content into chat
→ Claude responds with email query
→ User runs query manually, pastes result
→ Claude gives next step
```

**With Jira + PostgreSQL MCP servers:**
```
User: "Find the user email mentioned in JIRA issue ENG-4521"
→ Claude calls Jira MCP server: reads ENG-4521
→ Claude calls PostgreSQL MCP server: queries matching email
→ Claude returns result in one turn
```

## Notes & links

- Governance shift (Dec 2025): MCP moved to the Linux Foundation's Agentic AI Foundation, with OpenAI and Block as co-founders. Now vendor-neutral, not Anthropic-owned.
- Adoption scale: 10,000+ active public MCP servers as of early 2026; Python and TypeScript SDKs see ~97 million monthly downloads.
- Related: [[mcp-applications]] (richer extension mechanism), [[claude-code-mcp-server]] (expose Claude as a server)
