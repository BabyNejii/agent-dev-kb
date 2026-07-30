---
id: mcp-code-api-over-tools
title: Use code APIs instead of tool definitions for MCP servers
category: context
ecosystems: [mcp, claude-code, claude-sdk]
problem: Loading all MCP tool definitions upfront consumes 25-72% of context window before any real work; agents need progressive disclosure of capabilities
maturity: emerging
confidence: reported
effort_to_adopt: high
works_with: []
supersedes: []
sources:
  - {url: "https://www.anthropic.com/engineering/code-execution-with-mcp", kind: docs, date: "2026-07-28"}
  - {url: "https://dev.to/amzani/your-mcp-server-is-eating-your-context-window-theres-a-simpler-way-3ja2", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

The Model Context Protocol connects agents to many services, but scaling creates context waste. MCP clients load all tool definitions upfront. One example: three services with 40 tools total consumed 55,000 tokens before the agent read a user message (27% of 200K). An extreme case saw 143,000 of 200,000 tokens (72%) spent on tool definitions alone. Each tool call and result flows back through the model for reprocessing. Long data (2-hour transcripts) can add 50,000+ tokens per call.

## How it works

Instead of direct tool calls, present MCP servers as **code APIs** the agent can program against. The agent writes code to interact with the service, making use of conditionals, loops, and data filtering natively in the code execution environment rather than round-tripping through the model.

**Example pattern:** Replace a 50-tool API spec with a discoverable file tree. Each tool becomes a file (e.g., `getDocument.ts`) the agent can explore and load on-demand via `ls` or a lightweight `search_tools` endpoint. The agent learns what's available as it works, not before it starts.

This trades upfront cost for request-time latency and complexity, but reduces context footprint dramatically.

## Setup

**1. Expose MCP servers as code APIs:**

Instead of converting an entire API to MCP tools, create wrapper files:
```typescript
// getDocument.ts - explores tool definitions on-demand
export async function getDocument(docId: string) {
  return await client.api.documents.get(docId);
}

// listDocuments.ts - lightweight discovery
export async function listDocuments(filter?: {limit: number}) {
  return await client.api.documents.list(filter);
}
```

**2. Agent discovers and uses via code:**

```javascript
// Agent writes code to explore, not tool definitions
const docs = await listDocuments({limit: 10});
const filtered = docs.filter(d => d.updated > "2026-07-01");
return filtered.map(d => ({id: d.id, title: d.title}));
```

**3. Optional progressive disclosure via `search_tools`:**

Implement a lightweight `search_tools` API the agent can query:
```python
# Agent queries available tools
tools = search_tools("document", detail="minimal")
# Returns: [{name: "getDocument", desc: "Fetch a doc by ID"}, ...]

# Then calls only what it needs
details = search_tools("document", detail="full")
# Returns: [{name: "...", params: {...}, examples: [...]}]
```

**4. Results stay in execution environment:**

Large data transformations happen in code, not in the model:
```python
# Read 10,000 rows, filter to 10, only those reach the model
large_result = query_database()
filtered = [r for r in large_result if r.status == "active"][:10]
return filtered  # Only 10 rows tokenized
```

## When to use / when NOT

**Use when:**
- Connecting to APIs with 50+ endpoints
- Results are large (transcripts, file contents, query results)
- Agents need to filter, loop, or transform data before returning
- Context efficiency is critical for cost or latency

**NOT when:**
- Simple, few-tool integrations (direct tool calls are simpler)
- Code execution environment unavailable or untrusted
- Tight latency requirements (code execution adds round-trip latency)
- Tool schemas change frequently (requires maintaining code wrappers)

## Tradeoffs

**Strengths:**
- 95%+ reduction in upfront context cost (150K → 2K tokens reported)
- Progressive disclosure—agent learns capabilities on-demand
- Natural control flow (loops, conditions) in code, not prompt instructions
- Data filtering in code before tokenization (saves intermediate results)
- State persistence—agents save working code as reusable functions

**Weaknesses:**
- Higher implementation complexity (code wrappers vs. tool definitions)
- Added latency per discovery/call (round-trip through code execution)
- Requires secure execution environment with proper sandboxing
- Agents must write/read code; less natural for non-developer users
- Monitoring and debugging becomes harder

**When NOT worth it:**
- Small APIs (5-10 tools); direct tools simpler
- Real-time latency-critical paths
- Tools with complex, frequently-changing schemas

## Example

**Traditional MCP approach (context-heavy):**
```
Agent receives:
- 50 tool definitions (~30K tokens)
- 50 descriptions (~5K tokens)
- System prompt (~5K tokens)
= ~40K tokens before any real task

Context left: 160K / 200K
```

**Code API approach (context-light):**
```
Agent receives:
- 1 discovery function (~200 tokens)
- Light system prompt (~2K tokens)
= ~2.2K tokens before any task

Context left: 197.8K / 200K

Agent workflow:
1. Call search_tools("document") → get descriptions
2. Write code to filter/transform
3. Execute in sandbox
4. Return results
```

Sample code wrapper for Slack API:
```python
# slack_api.py wrapper — agent loads/calls as needed
class SlackAPI:
    def __init__(self, client):
        self.client = client
    
    async def get_channels(self, limit=10):
        result = await self.client.conversations_list(limit=limit)
        return result.get("channels", [])
    
    async def search_messages(self, query, limit=5):
        result = await self.client.search_messages(query=query, count=limit)
        return result.get("messages", {}).get("matches", [])

# Agent explores what's available
slack = SlackAPI(client)
channels = await slack.get_channels()  # Only requests what it needs
```

## Notes & links

- **Cloudflare's "Code Mode":** Similar pattern—treating APIs as code libraries agents program against, achieving massive context savings.
- **Hybrid approach:** For essential frequently-used tools, keep them as direct MCP tools; use code APIs for exploratory/optional integrations.
- **Discovery cost:** If agents must query for schema repeatedly, cache tool descriptions in memory or use a lightweight indexing layer.
- **Execution limits:** Set resource limits on code execution (timeouts, memory) to prevent runaway queries from consuming large datasets.
- Trade latency for tokens: Each discovery query adds a round-trip, but total tokens saved often outweighs latency cost for batch/agentic workflows.

See also: [[prompt-caching-with-claude-api]], [[context-compaction-beta]]
