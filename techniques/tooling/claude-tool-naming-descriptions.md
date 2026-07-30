---
id: claude-tool-naming-descriptions
title: Tool Naming and Descriptions for Accurate Agent Routing
category: tooling
ecosystems: [claude-code, claude-api]
problem: Ambiguous tool names and vague descriptions cause agents to misroute, pick wrong tools, or waste tokens deciding.
maturity: established
confidence: verified
effort_to_adopt: low
works_with: [mcp-tool-design-principles]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools", kind: docs, date: "2026-07-28"}
  - {url: "https://www.anthropic.com/engineering/writing-tools-for-agents", kind: docs, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Tool descriptions are the single most impactful factor in agent performance. Vague descriptions ("get data") cause agents to pick the wrong tool, waste context debating which tool to use, or call tools with incomplete parameters. Ambiguous names like `process_data` or `handle_request` multiply this confusion across a tool library.

## How it works

When an agent encounters a user request, it reads tool descriptions (loaded into its system prompt context) to decide which tool to invoke. Detailed descriptions that explain purpose, usage, caveats, and return values help agents route correctly on the first try. Conversely, single-sentence descriptions or unclear names force retries and context waste.

Tool names serve humans (for typing, recall, documentation); descriptions serve the agent (for routing, auto-discovery, behavior understanding).

## Setup

**1. Name tools with semantic prefixes and resource clarity**

Use resource-prefixed kebab-case (lowercase, hyphens, no abbreviations unless universal):

```
Good:
- github_list_pull_requests
- github_create_pull_request
- slack_send_message
- slack_list_channels
- db_query
- db_insert
- storage_read_file
- storage_write_file

Bad:
- list_prs (unclear what "prs" are without context)
- send_msg (abbreviation vague)
- process_data (what data? how?)
- handle_request (too generic)
- exec (does not indicate what executes)
```

**Constraint**: Names must match `^[a-zA-Z0-9_-]{1,64}$` (alphanumeric, underscores, hyphens, max 64 chars).

**2. Write descriptions with full context (3-4+ sentences minimum)**

Descriptions are loaded into the system prompt, so every character counts. Include:
- **What**: Clear purpose statement
- **When**: Ideal use cases
- **When NOT**: Important limitations or exclusions
- **Parameters**: What each input does and how it affects behavior
- **Caveats**: What information is NOT returned
- **Examples** (if complex): typical invocation patterns

```
Minimal description (poor):
"Get weather data for a location."

Full description (good):
"Retrieves the current weather in a given location. Use this tool when the user asks about current weather, temperature, or conditions. The location must be a valid city name or 'City, State' format (e.g., 'San Francisco, CA'). Returns current temperature in the requested unit (celsius or fahrenheit), wind speed, precipitation chance, and a brief condition summary. This tool does NOT provide historical weather data, forecasts, or alerts. If the location is not found, returns an error with suggestions for similar location names."
```

**3. Be explicit about parameter behavior**

For each parameter, explain its effect:

```json
{
  "name": "github_search_issues",
  "description": "Search for GitHub issues across one or more repositories by keyword, label, status, or other filters. Supports exact phrase matching, boolean operators (AND/OR/NOT), and wildcard patterns. Returns a paginated list of matching issues sorted by relevance (default) or other criteria.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query. Use exact phrases in quotes (e.g., '\"bug fix\"'), boolean operators (e.g., 'label:bug AND state:open'), or wildcards (e.g., 'auth*'). Required."
      },
      "repos": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of repository names (format: owner/repo). If empty, searches all public repos. If specified, searches only these repos."
      },
      "sort": {
        "type": "string",
        "enum": ["relevance", "created", "updated", "comments"],
        "description": "Sort order for results. 'relevance' (default) ranks by how well the issue matches the query. 'created' and 'updated' sort by date. 'comments' sorts by comment count."
      },
      "limit": {
        "type": "integer",
        "description": "Max issues to return (1-100, default 20). Larger limits may increase response time."
      }
    },
    "required": ["query"]
  }
}
```

**4. Consolidate similar operations to reduce tool count**

As tools accumulate, agents struggle deciding which to call. Consolidate with action parameters:

```
Poor approach (6 tools):
- user_create
- user_update
- user_get
- user_list
- user_delete
- user_search

Good approach (1 tool with actions):
- user_manager (actions: create, update, get, list, delete, search)
```

When you have 10+ similar tools, the agent's overhead in deciding which to call outweighs the clarity of separate tools.

**5. Indicate what information is returned and NOT returned**

This prevents agents from making unnecessary follow-up calls:

```
"Returns: order ID, status (confirmed/pending/cancelled), total price, and estimated delivery date. Does NOT include item details, customer name, or payment method. Use order_get_details to retrieve full item information if needed."

vs.

"Returns order information." (vague — agent may call multiple times)
```

**6. Use input_examples for complex tools**

For tools with nested objects, multiple optional parameters, or format-sensitive inputs, provide validated example invocations:

```json
{
  "name": "file_search",
  "description": "Search for files by name, content, or metadata. Supports glob patterns for recursive directory matching and regex for content search. Returns file paths and context snippets.",
  "input_schema": {...},
  "input_examples": [
    {
      "path": "src/**/*.ts",
      "content_regex": "TODO|FIXME",
      "limit": 50
    },
    {
      "path": "docs",
      "name_pattern": "*README*"
    },
    {
      "path": ".",
      "content_contains": "error handler",
      "file_type": ".py"
    }
  ]
}
```

## When to use / when NOT

**Use semantic resource prefixes:**
- Multi-service tool libraries (GitHub, Slack, databases)
- Any library with >5 tools
- Tools that will be browsed by humans

**Keep names short when:**
- Single-purpose tool libraries (<5 tools in total)
- Internal/private tools with domain context
- Still maintain clarity — "send_email" is fine; "snd_eml" is not

## Tradeoffs

- **Namespacing verbosity vs. brevity**: Prefixes like `github_` add characters but dramatically reduce ambiguity. Worth the cost.
- **Description length vs. token efficiency**: Longer descriptions consume more tokens during tool discovery. Balance detail with conciseness — aim for 3-4 sentences, add detail only for complex tools.
- **Parameter granularity vs. tool count**: Fine-grained parameters (separate tools for each operation) create many similar tools; consolidated tools with action parameters reduce confusion but require longer descriptions.

## Example

A well-named and well-described tool for email:

```json
{
  "name": "email_send",
  "description": "Send an email to one or more recipients. Supports plain text and HTML bodies, attachments, and CC/BCC. Includes built-in rate limiting: max 100 emails per minute per API key. Returns a delivery confirmation or error. Use this when the user requests to send an email, notify someone, or distribute a message. This tool does NOT support scheduling future sends, templating, or bulk recipient imports; use email_send_batch for multiple recipients. Attachments are limited to 25MB total per email.",
  "input_schema": {
    "type": "object",
    "properties": {
      "to": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Email addresses of primary recipients (e.g., ['user@example.com']). At least one required."
      },
      "subject": {
        "type": "string",
        "description": "Email subject line. Required. Max 200 characters."
      },
      "body": {
        "type": "string",
        "description": "Email body. Required. Plain text or HTML (detected automatically)."
      },
      "cc": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Email addresses to CC (optional). Defaults to empty."
      },
      "bcc": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Email addresses to BCC (optional, hidden from recipients). Defaults to empty."
      },
      "attachments": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "filename": {"type": "string", "description": "Name of the file as it appears to recipient"},
            "content": {"type": "string", "description": "Base64-encoded file content"}
          }
        },
        "description": "File attachments (optional). Max 25MB total."
      }
    },
    "required": ["to", "subject", "body"]
  },
  "input_examples": [
    {
      "to": ["user@example.com"],
      "subject": "Project Update",
      "body": "Here is the latest status..."
    },
    {
      "to": ["team@example.com"],
      "cc": ["manager@example.com"],
      "subject": "Weekly Report",
      "body": "<html><body><h1>Summary</h1><p>Details here.</p></body></html>",
      "attachments": [
        {
          "filename": "report.pdf",
          "content": "JVBERi0xLjQKJeLj..."
        }
      ]
    }
  ]
}
```

## Notes & links

- **Descriptions matter most**: Official Anthropic docs emphasize that description quality is the single highest-impact factor in tool performance.
- For tool structure and composability design, see [[mcp-tool-design-principles]].
- Anthropic's ["Writing Tools for Agents"](https://www.anthropic.com/engineering/writing-tools-for-agents) provides deep examples of good vs. poor tool definitions.
- When tool names conflict across systems (e.g., Claude SDK uses `mcp__` prefix while Agent Skills use `Server:` notation), document the naming convention in your team's guidelines.
