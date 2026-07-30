---
id: claude-code-jsonl-session-logs
title: Local JSONL session logging for agent debugging and cost analysis
category: operations
ecosystems: [claude-code, claude-sdk]
problem: When an agent misbehaves or costs spike, there is no local record of what it did, what tokens it spent, or what decisions it made
maturity: established
confidence: verified
effort_to_adopt: low
works_with: [agent-sdk-otel-observability, multi-agent-cost-attribution-sdk, action-cache-replay]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/monitoring-usage", kind: docs, date: 2026-07-30}
  - {url: "https://code.claude.com/docs/en/costs", kind: docs, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

Claude Code automatically logs every session to disk as JSONL files, but many users don't know these logs exist or don't know how to query them. This creates a blind spot:

- When an agent produces unexpected output, you have no trace of what it was thinking
- When costs spike, you can't see which commands or tool calls triggered the increase
- When debugging a multi-session workflow, you need to manually correlate events across different agent runs
- You cannot replay a session to reproduce a bug deterministically

Local JSONL logs are the raw truth: they capture every token count, every model request, every tool call, and every prompt/response pair (if logging is enabled). They sit on disk in `~/.claude/projects/` and cost nothing to produce.

## How it works

**Automatic logging:**
Claude Code writes one JSONL file per session to `~/.claude/projects/<project-id>/<session-id>.jsonl`. Each line is a structured event:

```json
{"type": "session_start", "timestamp": "2026-07-30T14:22:00Z", "model": "claude-3-5-sonnet-20241022", "session_id": "..."}
{"type": "llm_request", "timestamp": "...", "prompt_tokens": 2500, "completion_tokens": 1200, "cache_read_tokens": 0, "cache_creation_tokens": 1500}
{"type": "tool_call", "timestamp": "...", "tool_name": "bash", "command": "npm test"}
{"type": "tool_result", "timestamp": "...", "tool_name": "bash", "output": "PASS", "exit_code": 0}
{"type": "session_end", "timestamp": "...", "total_tokens": 5000, "estimated_cost": 0.0152}
```

**Querying and analysis:**
Parse these logs with `jq`, Python, or a simple script to:
- Sum token usage across a session or project
- Filter for specific tool calls (e.g., all Bash commands)
- Identify error patterns (failed tools, API errors, permission denials)
- Build a timeline of agent decisions
- Export to CSV for spreadsheet analysis

**Third-party dashboards:**
Community tools like `claude-usage` and `ccusage` read these JSONL logs and produce:
- Daily/monthly cost breakdowns
- Per-model spending comparisons
- Cost trend graphs
- Session duration and success rate statistics

## Setup

### Finding your logs

Claude Code logs go to:
- **macOS/Linux:** `~/.claude/projects/`
- **Windows:** `%USERPROFILE%\.claude\projects\`

Structure:
```
~/.claude/projects/
  <project-hash-1>/
    <session-id-1>.jsonl
    <session-id-2>.jsonl
  <project-hash-2>/
    ...
```

Each JSONL file is one session. File names are session IDs (often timestamps or UUIDs).

### Querying with `jq`

**Get total token usage for a session:**
```bash
jq 'select(.type == "llm_request") | .prompt_tokens + .completion_tokens' ~/.claude/projects/<project>/<session>.jsonl | paste -sd+ | bc
```

**Find all Bash commands executed:**
```bash
jq 'select(.type == "tool_call" and .tool_name == "bash") | .command' ~/.claude/projects/<project>/<session>.jsonl
```

**Extract token usage with timestamps:**
```bash
jq 'select(.type == "llm_request") | {timestamp, prompt_tokens, completion_tokens}' ~/.claude/projects/<project>/<session>.jsonl
```

**Count tool calls by type:**
```bash
jq 'select(.type == "tool_call") | .tool_name' ~/.claude/projects/<project>/<session>.jsonl | sort | uniq -c
```

### Parsing with Python

```python
import json
from pathlib import Path
from collections import defaultdict

def analyze_session(session_file: str):
    """Parse a JSONL session log and extract summary stats."""
    
    session_data = {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "tool_calls": defaultdict(int),
        "errors": [],
        "start_time": None,
        "end_time": None,
    }
    
    with open(session_file) as f:
        for line in f:
            event = json.loads(line)
            
            if event["type"] == "session_start":
                session_data["start_time"] = event.get("timestamp")
                session_data["model"] = event.get("model")
            
            elif event["type"] == "llm_request":
                session_data["total_input_tokens"] += event.get("prompt_tokens", 0)
                session_data["total_output_tokens"] += event.get("completion_tokens", 0)
            
            elif event["type"] == "tool_call":
                tool = event.get("tool_name", "unknown")
                session_data["tool_calls"][tool] += 1
            
            elif event["type"] == "error":
                session_data["errors"].append({
                    "timestamp": event.get("timestamp"),
                    "error": event.get("message"),
                })
            
            elif event["type"] == "session_end":
                session_data["end_time"] = event.get("timestamp")
                session_data["estimated_cost"] = event.get("estimated_cost", 0)
    
    return session_data

# Usage
session_file = Path.home() / ".claude" / "projects" / "<project-hash>" / "<session-id>.jsonl"
stats = analyze_session(str(session_file))

print(f"Model: {stats['model']}")
print(f"Tokens: {stats['total_input_tokens']} input, {stats['total_output_tokens']} output")
print(f"Estimated cost: ${stats['estimated_cost']:.4f}")
print(f"Tool calls: {dict(stats['tool_calls'])}")
if stats['errors']:
    print(f"Errors: {stats['errors']}")
```

### Enabling content logging (opt-in)

By default, JSONL logs omit prompt/response text (to preserve privacy). To enable content logging for debugging:

**Claude Code CLI:**
```bash
export CLAUDE_CODE_LOG_CONTENT=1
claude
```

**Agent SDK (Python):**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    env={
        "CLAUDE_CODE_LOG_CONTENT": "1",  # Include prompt/response text in local logs
    }
)

async for message in query(..., options=options):
    ...
```

Then JSONL events will include `prompt_text`, `response_text`, and `tool_input` fields.

**Warning:** Content logging creates larger log files and may capture sensitive information (API keys in logs, user data in prompts). Only enable when necessary for debugging and ensure logs are stored securely.

### Automating log collection and analysis

```bash
#!/bin/bash
# daily-agent-cost-report.sh
# Run daily to summarize Claude Code costs across all projects

report_date=$(date +%Y-%m-%d)
output_file="agent-costs-$report_date.csv"

echo "project,session_id,model,total_tokens,input_tokens,output_tokens,estimated_cost,duration" > "$output_file"

for project_dir in ~/.claude/projects/*/; do
    project_id=$(basename "$project_dir")
    
    for session_file in "$project_dir"*.jsonl; do
        session_id=$(basename "$session_file" .jsonl)
        
        # Parse with jq
        stats=$(jq -s '{
            model: (.[0].model // "unknown"),
            input_tokens: ([.[] | select(.type == "llm_request") | .prompt_tokens] | add),
            output_tokens: ([.[] | select(.type == "llm_request") | .completion_tokens] | add),
            cost: (.[0] | select(.type == "session_end") | .estimated_cost),
            start: (.[0].timestamp),
            end: (.[-1].timestamp)
        }' "$session_file")
        
        model=$(echo "$stats" | jq -r '.model')
        input_tokens=$(echo "$stats" | jq '.input_tokens // 0')
        output_tokens=$(echo "$stats" | jq '.output_tokens // 0')
        cost=$(echo "$stats" | jq '.cost // 0')
        total_tokens=$((input_tokens + output_tokens))
        
        echo "$project_id,$session_id,$model,$total_tokens,$input_tokens,$output_tokens,$cost" >> "$output_file"
    done
done

echo "Report written to $output_file"
```

Run with `cron`:
```bash
0 7 * * * /path/to/daily-agent-cost-report.sh
```

## When to use / when NOT

**Use this when:**
- You need to debug agent behavior without an external observability backend
- You want local, cost-free cost tracking (JSONL logs are always written)
- You're investigating a specific session and need detailed event timelines
- You want to build custom analytics on top of raw log data
- You're running Claude Code locally or in an environment without external observability infrastructure

**Do not use when:**
- You need real-time alerts (JSONL logs are only written to disk after a session completes or flushes)
- You want centralized cost tracking across a large team (use Agent SDK cost tracking or OpenTelemetry for aggregate visibility)
- You're running 100+ agents per day and need sub-second query latency (log files are text-based and require parsing)

## Tradeoffs

**Advantages:**
- Always-on, zero-configuration logging (no setup needed)
- Completely local — no data sent to external backends
- No privacy concerns (logs stay on your machine by default)
- Easy to query with `jq` or custom scripts
- Third-party dashboard tools exist for common analysis patterns
- Low storage footprint (JSONL is compact; typical session ≈ 5-10 KB)

**Disadvantages:**
- JSONL logs are per-session, per-project; correlating across sessions requires custom scripting
- Logs are written to disk after session completion (not real-time)
- Timestamps are relative to local time; correlating with server logs may require time-zone conversion
- No built-in alerting (you must write custom detection logic for anomalies)
- Disk cleanup is manual (logs accumulate over time; old ones are not auto-rotated)

## Example

**Detecting a runaway agent (excessive token usage):**

```python
import json
from pathlib import Path

def find_expensive_sessions(project_dir: str, token_threshold: int = 100000):
    """Find sessions that used more than threshold tokens."""
    
    expensive = []
    
    for session_file in Path(project_dir).glob("*.jsonl"):
        total_tokens = 0
        model = "unknown"
        cost = 0.0
        
        with open(session_file) as f:
            for line in f:
                event = json.loads(line)
                if event["type"] == "llm_request":
                    total_tokens += event.get("completion_tokens", 0) + event.get("prompt_tokens", 0)
                if event["type"] == "session_start":
                    model = event.get("model")
                if event["type"] == "session_end":
                    cost = event.get("estimated_cost", 0)
        
        if total_tokens > token_threshold:
            expensive.append({
                "session_id": session_file.stem,
                "model": model,
                "total_tokens": total_tokens,
                "estimated_cost": cost,
            })
    
    return sorted(expensive, key=lambda x: x["total_tokens"], reverse=True)

# Find sessions that burned >200k tokens
expensive = find_expensive_sessions("~/.claude/projects/<project-hash>", token_threshold=200000)
for session in expensive:
    print(f"{session['session_id']}: {session['total_tokens']} tokens (~${session['estimated_cost']:.2f})")
```

## Notes & links

- [[agent-sdk-otel-observability]] — for production observability with external backends
- [[multi-agent-cost-attribution-sdk]] — for programmatic cost tracking in Agent SDK
- [[action-cache-replay]] — for deterministic replay of tool calls using logged events
- **Third-party tools:**
  - `claude-usage` (GitHub: phuryn/claude-usage) — web dashboard and VS Code extension for log analysis
  - `ccusage` — CLI tool for quick cost summaries
- **Log location:** `~/.claude/projects/` on all platforms (Windows: `%USERPROFILE%\.claude\projects\`)
- **Cleanup:** JSONL files accumulate over time. Periodically delete old logs: `find ~/.claude/projects -name "*.jsonl" -mtime +90 -delete` (delete logs older than 90 days)
- **Privacy:** By default, JSONL logs omit content. Enabling `CLAUDE_CODE_LOG_CONTENT=1` includes full prompts/responses — only do this for debugging and keep logs secure.
