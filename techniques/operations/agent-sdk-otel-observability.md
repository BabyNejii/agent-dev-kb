---
id: agent-sdk-otel-observability
title: OpenTelemetry observability for Agent SDK deployments
category: operations
ecosystems: [claude-sdk, claude-code, claude-api]
problem: Running agents without observability means you cannot see what they're doing, where they fail, or how much they're costing in production
maturity: established
confidence: verified
effort_to_adopt: medium
works_with: [multi-agent-cost-attribution-sdk, claude-code-jsonl-session-logs]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/agent-sdk/observability", kind: docs, date: 2026-07-30}
  - {url: "https://code.claude.com/docs/en/monitoring-usage", kind: docs, date: 2026-07-30}
  - {url: "https://platform.claude.com/docs/en/managed-agents/observability", kind: docs, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

Agent runs in production are opaque: you cannot see what the agent is deciding, which tools it's calling, how long each step takes, where failures occur, or detailed token/cost breakdowns. This blindness becomes critical when:
- A deployed agent behavior changes unexpectedly
- Cost spikes and you need to understand which agents or operations drove it
- A user reports an issue and you need to replay exactly what happened
- You want to optimize agent performance but have no latency or decision data

## How it works

Claude Code and the Agent SDK have OpenTelemetry (OTel) instrumentation built in. When you enable telemetry:

1. **Traces** capture the full agent interaction timeline as nested spans:
   - `claude_code.interaction` — a single turn of the agent loop (prompt → response)
   - `claude_code.llm_request` — each API call to Claude, with latency and token counts
   - `claude_code.tool` — each tool invocation (file edit, Bash, MCP call, etc.)
   - `claude_code.hook` — execution of pre/post-hooks (with beta tracing enabled)

2. **Metrics** are counters exported on a configurable interval:
   - Token usage (input, output, cache reads/writes)
   - Estimated cost
   - Session and interaction counts
   - Lines of code written
   - Tool decision breakdown

3. **Log events** are structured records for every prompt, API response, tool result, and error:
   - `claude_code.user_prompt` — the input prompt (opt-in: requires `OTEL_LOG_USER_PROMPTS=1`)
   - `claude_code.tool_result` — tool outputs with input arguments (opt-in)
   - `claude_code.api_request_body` / `api_response_body` — full API bodies (opt-in)

All three signals are independent: you can enable just metrics, just logs, or all three. Data is exported to any OTLP-compatible backend (Honeycomb, Datadog, Grafana, Langfuse, or a self-hosted collector).

## Setup

### Prerequisites
- Claude SDK v2.1.160+ (or Claude Code CLI v2.1.160+)
- An OTLP receiver (e.g., Datadog, Honeycomb, local `otel-collector`)

### Basic setup (Agent SDK, Python)

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

OTEL_ENV = {
    # Enable telemetry globally (required)
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    
    # Enable beta tracing (required for traces; metrics/logs work without it)
    "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA": "1",
    
    # Choose exporters (comma-separated, can use one or all three)
    "OTEL_TRACES_EXPORTER": "otlp",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    
    # Configure OTLP endpoint (required for otlp exporter)
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",  # or grpc, http/json
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
    
    # Authentication (if required by your backend)
    "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Bearer your-token",
    
    # For short-lived tasks, flush telemetry more frequently
    "OTEL_METRIC_EXPORT_INTERVAL": "1000",    # 1 second (default: 60s)
    "OTEL_LOGS_EXPORT_INTERVAL": "1000",      # 1 second (default: 5s)
    "OTEL_TRACES_EXPORT_INTERVAL": "1000",    # 1 second (default: 5s)
    
    # Tag the service in your backend (optional)
    "OTEL_SERVICE_NAME": "customer-support-agent",
    
    # Attach deployment metadata as resource attributes (optional)
    "OTEL_RESOURCE_ATTRIBUTES": "service.version=1.2.0,deployment.environment=production",
}

async def main():
    options = ClaudeAgentOptions(env=OTEL_ENV)
    async for message in query(
        prompt="Analyze the customer feedback in /data/feedback.txt and summarize trends",
        options=options
    ):
        print(message)

asyncio.run(main())
```

**Environment variables** (set in shell/container instead of code):
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
export OTEL_TRACES_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=http://collector.example.com:4318
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer your-token"
export OTEL_SERVICE_NAME=my-agent
```

### Tagging runs with end-user identity (for SIEM integration)

To attribute tool calls and decisions to your application's end users:

```python
from urllib.parse import quote

# Attach end-user identity so audit events are per-user
options = ClaudeAgentOptions(
    env={
        **OTEL_ENV,
        "OTEL_RESOURCE_ATTRIBUTES": f"enduser.id={quote(user_id)},tenant.id={quote(tenant_id)},service.version=1.2.0",
    }
)
```

### Content logging (opt-in)

By default, telemetry is structural (no sensitive content logged). To add content for debugging:

```python
OTEL_ENV.update({
    "OTEL_LOG_USER_PROMPTS": "1",           # Log input prompts
    "OTEL_LOG_TOOL_DETAILS": "1",           # Log tool args (file paths, commands)
    "OTEL_LOG_TOOL_CONTENT": "1",           # Log full tool input/output
    "OTEL_LOG_RAW_API_BODIES": "1",         # Log full API request/response JSON
})
```

**Only enable if your observability pipeline is approved to store the data your agent processes.**

## When to use / when NOT

**Use this when:**
- You are deploying agents to production where visibility into behavior is critical
- You want per-agent cost attribution and performance metrics
- You need an audit trail for compliance or security reviews
- You're debugging misbehavior and want detailed traces of decisions and tool calls
- You're running Agent SDK in a containerized environment with a centralized collector

**Do not use when:**
- You are experimenting locally with Claude Code (use `/cost` command instead, which is faster and always available)
- Your observability backend is not OTLP-compatible and you don't want to run an intermediary collector
- You cannot approve sensitive data exposure in your backend (leave content-logging vars unset)

## Tradeoffs

**Advantages:**
- Complete visibility into agent behavior and costs
- Works with any OTLP backend (no vendor lock-in)
- Token and cost data is authoritative (from API responses, not estimates)
- Traces nest subagent calls, so you see the full delegation chain
- W3C trace-context propagation links agent spans to your application's traces
- Audit events are suitable for SIEM platforms

**Disadvantages:**
- Requires configuring an external backend (or self-hosted collector)
- Export intervals add latency to span appearance in your backend (mitigated by lowering export intervals)
- Telemetry collection and export add minimal but nonzero overhead to agent execution
- Span and metric names/attributes are beta and may change between Claude Code releases
- Content logging (prompts, tool args) must be explicitly opted into and carries privacy considerations

## Example

**Monitoring a multi-tenant SaaS application with per-tenant cost attribution:**

```python
# settings.py / environment
OTEL_ENV = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA": "1",
    "OTEL_TRACES_EXPORTER": "otlp",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",  # faster than http/protobuf
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://api.honeycomb.io:443",
    "OTEL_EXPORTER_OTLP_HEADERS": f"Authorization=Bearer {HONEYCOMB_API_KEY}",
    "OTEL_SERVICE_NAME": "content-moderation-agent",
    "OTEL_METRIC_EXPORT_INTERVAL": "5000",  # 5 sec batches
}

# Within a web request handler
async def moderate_user_content(request, user_id, tenant_id, content):
    from urllib.parse import quote
    
    options = ClaudeAgentOptions(
        env={
            **OTEL_ENV,
            "OTEL_RESOURCE_ATTRIBUTES": f"user.id={quote(user_id)},tenant.id={quote(tenant_id)}",
        }
    )
    
    async for message in query(
        prompt=f"Moderate this content for policy violations: {content}",
        options=options
    ):
        if message.type == "final_response":
            return message.content
```

In Honeycomb, you can then:
- Filter traces by `attributes.user.id` or `attributes.tenant.id`
- Create a dashboard of metrics grouped by `tenant.id`
- Set up alerts when any tenant's token usage exceeds a threshold
- Export tool_decision and tool_result events to your SIEM with `mcp_server_connection` events

## Notes & links

- [[multi-agent-cost-attribution-sdk]] — for per-session cost accounting without an external backend
- [[claude-code-jsonl-session-logs]] — local JSONL logs as an alternative to telemetry export
- **Privacy note:** By default, telemetry omits prompt/response content. Setting content-logging vars requires explicit approval in your security/privacy review.
- **Beta warning:** Trace span names and attributes are subject to change. Avoid hardcoding span or attribute names in alerting or filtering logic.
- **Timing:** Export intervals (default: 60s for metrics, 5s for logs/traces) can cause short tasks to lose telemetry. Lower them for interactive testing; use defaults for long-running production tasks.
