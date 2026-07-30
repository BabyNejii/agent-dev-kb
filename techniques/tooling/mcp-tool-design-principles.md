---
id: mcp-tool-design-principles
title: Designing MCP Tools for Agent Clarity and Composability
category: tooling
ecosystems: [mcp, claude-code, claude-api]
problem: Poorly designed tools confuse agents and waste context through unclear purposes and fragmented operations.
maturity: established
confidence: verified
effort_to_adopt: medium
works_with: [mcp-error-handling-model-recovery, claude-tool-naming-descriptions]
supersedes: []
sources:
  - {url: "https://modelcontextprotocol.io/docs/concepts/tools/", kind: docs, date: "2026-07-28"}
  - {url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools", kind: docs, date: "2026-07-28"}
  - {url: "https://www.anthropic.com/engineering/writing-tools-for-agents", kind: docs, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

When tools lack clear purpose, fragment operations unnecessarily, or return bloated responses, agents waste tokens deciding which tool to call, misuse tools, or struggle to extract actionable results.

## How it works

MCP tools are agent-accessible functions defined by three components: a unique name (alphanumeric, hyphens, underscores; max 64 chars), a detailed description (the single most important factor in tool performance), and a JSON Schema input specification. The agent reads descriptions to decide when and how to invoke tools, then processes the result to determine its next step.

The design philosophy treats tools as composable primitives. Like Unix pipes, one tool's output should feed cleanly into another's input, batch operations should allow agents to act on multiple items in one call rather than looping one-at-a-time, and multiple abstraction levels let the agent pick the right granularity for the task.

## Setup

**1. Consolidate related operations**

Rather than creating separate tools for each action (create_order, update_order, cancel_order, get_order, list_orders, search_orders), group them into one or two tools with an `action` parameter:

```json
{
  "name": "order_manager",
  "description": "Manage orders: create new orders, update existing orders, cancel orders, retrieve order details by ID, list all orders, or search orders by criteria like date range or customer ID.",
  "input_schema": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["create", "update", "cancel", "get", "list", "search"],
        "description": "The operation to perform on an order"
      },
      "order_id": {
        "type": "string",
        "description": "Required for update, cancel, get actions"
      },
      "details": {
        "type": "object",
        "description": "Order details object for create/update (items, customer_id, status, etc.)"
      },
      "filter": {
        "type": "object",
        "description": "Search filters for list/search actions (date_range, customer_id, status, etc.)"
      }
    },
    "required": ["action"]
  }
}
```

**2. Write detailed descriptions (3-4+ sentences minimum)**

Descriptions are loaded into context so they heavily influence tool selection and usage. Include:
- What the tool does
- When to use it and when NOT to
- What each parameter affects
- Important caveats or limitations
- What information is NOT returned

```
Good: "Retrieves the current stock price for a given ticker symbol. The ticker must be a valid symbol for a publicly traded company on a major US stock exchange (NYSE/NASDAQ). Returns the latest trade price in USD only. Should be used when the user asks about current or most recent price; will NOT provide historical data, company info, or other metrics. If the ticker is invalid or not found, returns an error indicating the symbol was not recognized."

Poor: "Gets the stock price for a ticker."
```

**3. Use meaningful namespacing**

Prefix tool names with the resource or service they operate on:

```
github_list_prs
github_create_pr
github_merge_pr
slack_send_message
slack_list_channels
db_query
db_insert
storage_read
storage_write
```

**4. Design responses to return only high-signal information**

Return stable, semantic identifiers (slugs, UUIDs) rather than opaque internal references. Include only the fields the agent needs to determine its next step:

```json
// Good: semantic, minimal
{
  "order_id": "ORD-2026-789456",
  "status": "confirmed",
  "total_price": "$149.99"
}

// Poor: bloated, internal details
{
  "internal_order_ref": "db_rec_12847365",
  "customer_internal_id": 98765,
  "items_internal_refs": [1, 2, 3, 4],
  "all_customer_order_history": [...],
  "raw_json_metadata": {...}
}
```

**5. Support batch operations**

When an agent needs to act on multiple items, provide batch endpoints to avoid agent loops:

```json
{
  "name": "email_send_batch",
  "description": "Send emails to multiple recipients in a single call. More efficient than sending individual emails, reducing API calls and latency.",
  "input_schema": {
    "type": "object",
    "properties": {
      "emails": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"}
          },
          "required": ["to", "subject", "body"]
        },
        "minItems": 1,
        "maxItems": 100
      }
    },
    "required": ["emails"]
  }
}
```

## When to use / when NOT

**Use consolidated multi-action tools when:**
- Operations affect the same resource (orders, users, files)
- Agent flow often requires chaining multiple related operations
- Tool count is becoming unwieldy (>15 tools)

**Avoid consolidation when:**
- Operations have radically different parameters or error modes
- One operation is called far more frequently than others
- Security boundaries demand separation (e.g., read vs. write)

## Tradeoffs

- **Consolidation vs. clarity**: Combining too many actions obscures tool purpose. Balance with detailed descriptions.
- **Composability vs. convenience**: Unix-style piping is powerful but requires agents to chain calls. Provide higher-level "compound" tools for common workflows.
- **Response minimalism vs. completeness**: Returning only essential fields saves tokens but may force agents to make follow-up calls. Include secondary fields if they're frequently needed.

## Example

A well-designed database query tool:

```json
{
  "name": "db_query",
  "description": "Execute read-only SQL SELECT queries against the production database. Returns results as JSON. Supports pagination for large result sets. Max 1000 rows per query. Will NOT execute INSERT, UPDATE, DELETE, or DDL statements. Queries timeout after 30 seconds. Always use LIMIT to constrain results. Table schemas are available via the db_schema tool.",
  "input_schema": {
    "type": "object",
    "properties": {
      "sql": {
        "type": "string",
        "description": "SELECT query to execute. Must include LIMIT clause."
      },
      "limit": {
        "type": "integer",
        "description": "Max rows to return (1-1000, default 100)"
      },
      "offset": {
        "type": "integer",
        "description": "Pagination offset (default 0)"
      }
    },
    "required": ["sql"]
  },
  "input_examples": [
    {"sql": "SELECT id, name, email FROM users WHERE created_at > '2026-01-01' LIMIT 50"},
    {"sql": "SELECT * FROM orders WHERE customer_id = ? LIMIT 100", "offset": 100}
  ]
}
```

## Notes & links

- Anthropic's engineering blog post ["Writing Tools for Agents"](https://www.anthropic.com/engineering/writing-tools-for-agents) provides deep guidance on tool consolidation and response design.
- For error handling within tool responses, see [[mcp-error-handling-model-recovery]].
- For naming and description specifics, see [[claude-tool-naming-descriptions]].
- Fewer, well-designed tools outperform many fragmented tools. A library of 10 carefully consolidated tools beats 50 single-action tools.
