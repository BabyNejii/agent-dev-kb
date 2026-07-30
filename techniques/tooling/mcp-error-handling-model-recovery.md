---
id: mcp-error-handling-model-recovery
title: MCP Error Handling for Model Self-Correction
category: tooling
ecosystems: [mcp, claude-code, claude-api]
problem: Unhandled tool errors crash agents; structured errors enable models to recover intelligently.
maturity: established
confidence: verified
effort_to_adopt: medium
works_with: [mcp-tool-design-principles, claude-tool-naming-descriptions]
supersedes: []
sources:
  - {url: "https://modelcontextprotocol.io/docs/concepts/tools/", kind: docs, date: "2026-07-28"}
  - {url: "https://www.anthropic.com/engineering/writing-tools-for-agents", kind: docs, date: "2026-07-28"}
  - {url: "https://www.getknit.dev/blog/mcp-architecture-deep-dive-tools-resources-and-prompts-explained", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

When MCP tools fail, the error handling determines whether agents recover intelligently or fail. Crashing servers (protocol-level errors) end the conversation. Generic error messages ("Operation failed") provide no signal. Actionable, structured errors allow models to adjust strategy, retry, or request user intervention.

## How it works

MCP distinguishes between protocol-level errors (server crashes, malformed JSON) and application-level errors (business logic failures, API rate limits, invalid inputs). Application-level errors should always be reported within the tool result using the `isError` flag, never as protocol-level errors. This lets the model see the failure and respond appropriately.

The model's capabilities determine recovery: detailed error text ("rate limit exceeded; retry after 30 seconds") enables the model to wait or try alternatives; vague errors ("Operation failed") force blind retries or abandonment.

## Setup

**1. Distinguish error types and classify for recoverability**

Define which errors are retryable (transient) vs. permanent:

```python
# Retryable (transient) errors
- Rate limit exceeded → retry with exponential backoff
- Temporary network timeout → retry
- Database connection pool exhausted → retry with delay

# Permanent (non-retryable) errors
- Invalid input parameters → require correction
- Resource not found (404) → no retry
- Permission denied (403) → no retry
- Schema validation failure → require correction
```

**2. Return errors within the result object with isError flag**

Never raise protocol-level exceptions for business logic failures. Instead, structure the result:

```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Rate limit exceeded. This endpoint allows 100 requests per minute. You have made 102 requests in the last 60 seconds. Retry after 30 seconds or reduce batch size to 50 items per request."
    }
  ]
}
```

**3. Write actionable error messages**

Error messages should guide the agent toward recovery:

```
Bad: "Operation failed"
Good: "Database query timed out after 30 seconds. The WHERE clause may be too expensive. Try adding an index on the status column or splitting the query into smaller date ranges."

Bad: "Invalid input"
Good: "Invalid input: 'email' field must be a valid email address (example: user@domain.com). The provided value 'john_at_domain' does not match the email format."

Bad: "429"
Good: "Rate limited (429). This endpoint allows 10 requests per second per API key. Current rate: 15 requests/sec. Wait 2 seconds before retrying, or reduce concurrency."
```

**4. Include structured recovery hints in error responses**

For complex tools, add a `recovery_hint` or `retry_after` field:

```python
def handle_rate_limit_error():
    return {
        "isError": True,
        "content": [{
            "type": "text",
            "text": "Rate limit exceeded on GitHub API. Limit: 60 requests/hour. Remaining: 0. Resets at 2026-07-28 14:30:00 UTC.",
        }],
        "retry_after_seconds": 3600,
        "retryable": True
    }
```

**5. Validate inputs early with detailed error messages**

Use schema validation (Pydantic, JSON Schema) and report validation failures clearly:

```python
from pydantic import BaseModel, ValidationError, EmailStr

class EmailInput(BaseModel):
    email: EmailStr
    subject: str
    body: str

try:
    EmailInput(email="invalid-email", subject="Test", body="Body")
except ValidationError as e:
    error_details = "\n".join(
        f"Field '{err['loc'][0]}': {err['msg']}"
        for err in e.errors()
    )
    return {
        "isError": True,
        "content": [{
            "type": "text",
            "text": f"Input validation failed:\n{error_details}"
        }]
    }
```

**6. Implement layered error handling**

Structure error handling in layers: validate inputs first, catch specific exceptions, then catch-all for unexpected errors:

```python
def execute_tool(tool_input):
    try:
        # Layer 1: Input validation
        validated_input = MyToolInput(**tool_input)
    except ValidationError as e:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Invalid input: {e}"}]
        }
    
    try:
        # Layer 2: Execute with specific exception handling
        result = call_external_api(validated_input)
    except RateLimitError as e:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Rate limited. Retry after {e.reset_time} seconds."}],
            "retryable": True
        }
    except ResourceNotFoundError as e:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Not found: {e}"}],
            "retryable": False
        }
    except Exception as e:
        # Layer 3: Unexpected errors (log, don't expose internals)
        logger.error(f"Unexpected error in tool: {e}", exc_info=True)
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Unexpected error occurred. Check logs for details."}],
            "retryable": False
        }
    
    return {"content": [{"type": "text", "text": result}]}
```

**7. Never leak internal details in error messages**

Security principle: errors shown to the model must not expose internal architecture, stack traces, or database details:

```
Bad: "SQLException: Cannot insert NULL into column 'user_accounts.auth_token' at line 342 of db_handler.py"
Good: "User record is missing required authentication token. Ensure the user has completed the signup flow before attempting this operation."

Bad: "Connection refused to database server 10.2.1.5:5432"
Good: "Database service is temporarily unavailable. Please retry in a few moments."
```

## When to use / when NOT

**Always structure application-level errors this way:**
- Tool logic failures (validation, not found, permission denied)
- External API failures (rate limits, timeouts, auth failures)
- Resource constraint issues (quota exceeded, disk full)

**Never use for:**
- Protocol errors (malformed JSON, schema violations at the MCP layer — these should crash)
- Unrecoverable server crashes (use protocol errors)

## Tradeoffs

- **Verbosity vs. clarity**: Detailed error messages consume more tokens but enable recovery. For high-frequency errors, provide concise guidance.
- **Security vs. helpfulness**: Overly sanitized errors ("Something went wrong") are unhelpful; balanced errors expose the problem without leaking internals.
- **Retry strategy overhead**: Exponential backoff prevents server hammering but adds latency. Use appropriate backoff curves for your SLAs.

## Example

A production-grade database query error handler:

```python
def query_database(sql: str, limit: int = 100) -> dict:
    try:
        # Validate SQL
        if not sql.strip().upper().startswith("SELECT"):
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": "Only SELECT queries are allowed. INSERT, UPDATE, DELETE, and DDL statements are not supported."
                }],
                "retryable": False
            }
        
        # Execute query
        results = db.execute(sql, timeout=30)
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(results[:limit], default=str)
            }]
        }
    
    except db.TimeoutError:
        return {
            "isError": True,
            "content": [{
                "type": "text",
                "text": "Query timeout after 30 seconds. The query may be inefficient. Try: (1) adding LIMIT, (2) indexing the WHERE clause columns, (3) splitting into smaller queries by date range."
            }],
            "retryable": True,
            "retry_after_seconds": 60
        }
    
    except db.NotFoundError as e:
        return {
            "isError": True,
            "content": [{
                "type": "text",
                "text": f"Table or column not found: '{e.resource}'. Use the db_schema tool to list available tables and columns."
            }],
            "retryable": False
        }
    
    except Exception as e:
        logger.error(f"Unexpected database error: {e}", exc_info=True)
        return {
            "isError": True,
            "content": [{
                "type": "text",
                "text": "Unexpected database error. Please check your query syntax and try again."
            }],
            "retryable": False
        }
```

## Notes & links

- The key principle: errors surface to the model as structured data in the result, not as exceptions that crash the server.
- For designing tools to work well with error handling, see [[mcp-tool-design-principles]].
- Anthropic's guidance on ["Writing Tools for Agents"](https://www.anthropic.com/engineering/writing-tools-for-agents) covers error design in detail.
- Test error paths as thoroughly as happy paths. A tool's robustness depends on its error handling.
