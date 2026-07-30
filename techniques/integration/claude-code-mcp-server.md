---
id: claude-code-mcp-server
title: Claude Code as an MCP server (exposing tools to other agents)
category: integration
ecosystems: [claude-code, mcp]
problem: Other agents can't access Claude Code's capabilities (file editing, bash, codebase search) directly
maturity: emerging
confidence: speculative
effort_to_adopt: low
works_with: [mcp-as-integration-layer]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/mcp", kind: docs, date: "2026-07-28"}
  - {url: "https://truthifi.com/education/state-of-mcp-2026-ai-agents-custom-connectors", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Claude Code has powerful tools: file editing, bash execution, codebase search, git commands. But other agents (Cursor, Copilot CLI, Antigravity) can't call these tools directly. If you're coordinating multiple agents, some agents are left without access to Claude Code's capabilities.

## How it works

Claude Code exposes its built-in tools as an MCP server via the command:
```bash
claude mcp serve
```

This starts Claude Code in server mode, allowing other MCP-compatible clients to call:
- **File operations**: Read, write, edit files in the project
- **Bash execution**: Run terminal commands
- **Codebase search**: Grep, symbol lookup, pattern matching
- **Git commands**: Stage, commit, push, branch operations

Other agents connect to this server and gain access to Claude Code's tools without reimplementing them.

**Architecture:**
```
Cursor/Copilot/Antigravity (MCP clients)
         ↓ MCP protocol
   Claude Code (MCP server)
         ↓ (has access to)
    File system + Bash + Git
```

## Setup

### Starting Claude Code as a server:
```bash
claude mcp serve [--host <host>] [--port <port>]
```

Default: localhost:8080 (stdio if no host specified)

### Connecting another agent:
In the other agent's MCP configuration, add:
```json
{
  "name": "claude-code",
  "type": "http",
  "url": "http://localhost:8080"
}
```

Or via CLI (if the agent supports it):
```bash
# Example: Cursor
cursor mcp add claude-code http://localhost:8080
```

## When to use / when NOT

- **USE** when coordinating multiple agents (Cursor + Claude Code) on the same project
- **USE** to share Claude Code's superior file-editing and codebase-search capabilities
- **USE** for agent orchestration where one agent (e.g., planner) delegates work to Claude Code (executor)
- **NOT** if all agents are Claude Code (no benefit to serving yourself)
- **NOT** if the other agent already has equivalent tools

## Tradeoffs

**Security:** Exposing your local tools (file edit, bash) to a network (even localhost) widens the attack surface. Only use if you trust all connected agents.

**Resource overhead:** Running Claude Code as a server consumes memory and attention. It's blocking—if it's handling a large file operation, it can't accept new requests.

**Reconnection logic:** Unlike HTTP MCP clients with built-in retry, stdio-based clients don't auto-reconnect if the server crashes. You'll need to restart manually or implement monitoring.

## Example

**Without Claude Code as a server:**
```
Cursor agent: "Add error logging to auth module"
→ Cursor tries to edit src/auth.ts
→ Cursor's file editing is less precise than Claude Code's
→ Edit succeeds but introduces formatting issues
```

**With Claude Code as a server:**
```
Cursor agent: "Add error logging to auth module"
→ Calls Claude Code MCP server: edit(file, changes)
→ Claude Code's precise editor applies changes
→ Edit succeeds with correct formatting
```

## Notes & links

- **Reverse MCP:** This is "reverse MCP"—instead of agents connecting to external tools, an agent exposes its tools for others to call. Relatively new pattern (2026).
- **Transport:** Currently supports stdio (local) and HTTP (remote). Future: SSH, WebSocket for better network robustness.
- **Use with orchestrators:** Pairs well with [[mcp-as-integration-layer]] for larger agent coordination systems.
- Related: [[mcp-applications]] (richer task semantics beyond tools)
