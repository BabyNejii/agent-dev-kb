---
id: postoolbatch-circuit-breaker-parallel-tasks
title: PostToolBatch circuit breaker to halt agent loops on cascading parallel failures
category: operations
ecosystems: [claude-code, claude-sdk]
problem: When agents fan out many parallel tool calls, a single failure or pattern of failures can cascade; the agent keeps retrying each branch instead of recognizing the systematic problem and stopping.
maturity: emerging
confidence: verified
effort_to_adopt: medium
works_with: [subagent-fan-out, supervisor-pattern, pretooluse-guards-dangerous-operations]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/hooks", kind: docs, date: "2026-07-30"}
added: "2026-07-30"
updated: "2026-07-30"
---

## Problem

An agent launches 50 parallel file reads via subagents. Half fail with "permission denied" because the agent lost credentials. Instead of recognizing the pattern and stopping, the agent logs each failure and tries 49 more times, wasting tokens and time. PreToolUse blocks individual calls; PostToolBatch fires after the entire batch completes, giving you a chance to inspect aggregate results and halt if needed.

## How it works

PostToolBatch fires after a full batch of parallel tool calls resolves. You inspect:
- How many calls succeeded vs. failed
- Error categories (all permission errors? all timeouts?)
- Whether retrying makes sense

If the pattern indicates a systemic problem (authentication lost, resource exhausted, rate-limited at the source), you can halt the agentic loop with `continue: false` before Claude issues more tool calls. This is distinct from blocking a single call — it stops the entire agent.

## Setup

**1. Create a hook script in `.claude/hooks/`**

```bash
#!/bin/bash
# .claude/hooks/detect-batch-failure.sh
input=$(cat)

# Parse the tool batch results
total=$(echo "$input" | jq '.tool_results | length')
failures=$(echo "$input" | jq '[.tool_results[] | select(.tool_result.isError == true)] | length')
success=$((total - failures))

# Check for patterns indicating a systematic problem
all_same_error=$(echo "$input" | jq '.tool_results[].tool_result.content[0].text' | sort | uniq -c | head -1)

# If >80% failed, likely a systematic issue
if (( failures * 100 / total > 80 )); then
  jq -n '{
    continue: false,
    stopReason: "Batch failure rate too high ('"$failures"'/'"$total"' failed). Likely systematic issue, not transient. Agent halted."
  }'
  exit 0
fi

# If all errors are the same, likely systematic (e.g., auth failure)
if echo "$input" | jq '.tool_results[] | select(.tool_result.isError == true)' | \
   jq -s 'group_by(.tool_result.content[0].text) | length' | grep -q '^1$'; then
  jq -n '{
    continue: false,
    stopReason: "All failures report the same error. Likely not a transient issue. Agent halted to avoid retry storm."
  }'
  exit 0
fi

# Otherwise, allow the loop to continue (agent can decide to retry)
exit 0
```

**2. Register in `.claude/settings.json`**

```json
{
  "hooks": {
    "PostToolBatch": [
      {
        "type": "command",
        "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/detect-batch-failure.sh",
        "args": []
      }
    ]
  }
}
```

**3. More sophisticated: graduated response**

Instead of binary halt, return advisories that Claude can see:

```bash
#!/bin/bash
# Graduated response based on batch health
input=$(cat)
failures=$(echo "$input" | jq '[.tool_results[] | select(.tool_result.isError == true)] | length')
total=$(echo "$input" | jq '.tool_results | length')
percent=$((failures * 100 / total))

if (( percent > 80 )); then
  # Critical: halt
  jq -n '{
    continue: false,
    stopReason: "'"$percent"'% failure rate. Systematic issue detected."
  }'
elif (( percent > 50 )); then
  # Warning: continue but signal to Claude
  jq -n '{
    continue: true,
    advisoryMessage: "'"$percent"'% of the batch failed. You may want to investigate before continuing."
  }'
else
  # Normal: proceed
  exit 0
fi
```

**4. Distinguish transient from permanent failures**

```bash
#!/bin/bash
# Inspect error messages to classify
input=$(cat)

transient_count=$(echo "$input" | jq '[.tool_results[] | select(.tool_result.content[0].text | contains("timeout") or contains("temporarily") or contains("503") or contains("rate limit"))] | length')
permanent_count=$(echo "$input" | jq '[.tool_results[] | select(.tool_result.content[0].text | contains("not found") or contains("403") or contains("400") or contains("invalid"))] | length')
total=$(echo "$input" | jq '.tool_results | length')

if (( permanent_count > 0 && transient_count == 0 )); then
  # All failures are permanent (not found, permission denied) — don't retry
  jq -n '{
    continue: false,
    stopReason: "All failures are permanent (not found / invalid). Retrying will not help."
  }'
elif (( permanent_count > 0 && transient_count > 0 )); then
  # Mixed — log for user decision
  echo "Mixed failure types: $permanent_count permanent, $transient_count transient" >&2
  exit 0  # let Claude decide
else
  # All transient — allow retry
  exit 0
fi
```

## When to use / when NOT

**Use PostToolBatch circuit breaker when:**
- Agent fans out many parallel calls (subagents, batch operations, file processing)
- Failures are likely to be systematic (auth lost, resource exhausted, rate-limited)
- Retrying after systemic failure is wasteful (will just fail the same way)
- You want to detect cascading failures early

**Do NOT use when:**
- Tool calls are serialized (one at a time) — PostToolUse is more appropriate
- Failures are expected and recovery is part of the workflow
- You want granular per-call decisions — that's PreToolUse

**Combine with other techniques:**
- **PreToolUse** for fine-grained blocking (e.g., prevent the first rm call)
- **PostToolUse** for per-call audit or result redaction
- **PostToolBatch** for aggregate decisions (stop if >80% failed)

## Tradeoffs

**Wins:** Detects cascading failures early, prevents token waste on pointless retries, gives agent a clear signal when to stop, scales better than per-call guards.

**Costs:** Requires hook logic to classify errors correctly (pattern matching is fragile), may be overly aggressive (legitimate transient failures could trigger a halt), adds latency (hook runs after every batch).

**Risk:** If your halt condition is too sensitive, you halt legitimate work. If too conservative, you waste tokens on retry storms.

## Example

```
Scenario: Subagent fan-out to read 10 files

Main agent:
  "I'll read the user config from 10 locations to find the active one"
  → Spawns 10 subagents to read: ~/.config/app.yaml, /etc/app.yaml, ~/app.yaml, etc.

Subagent results (after all 10 complete):
  ✓ 0 succeeded
  ✗ 10 failed with "permission denied"
  
PostToolBatch hook runs:
  Checks: failures = 10, total = 10, percent = 100%
  Checks: all errors identical ("permission denied")
  Decision: continue = false, stopReason = "All 10 reads failed with permission denied. Likely lost auth credentials."
  
Main agent sees:
  Circuit breaker halted the loop
  Reads error: "All 10 reads failed with permission denied..."
  Agent responds: "I don't have permission to read config files. Please check my credentials."

Scenario: Subagent batch processing with mixed failures

Agent:
  "I'll validate 50 JSON files in parallel"
  → Spawns 50 subagents, each validates one file

Results:
  ✓ 45 succeeded
  ✗ 5 failed with "not valid JSON"

PostToolBatch hook:
  failures = 5, total = 50, percent = 10%
  Classified: 5 permanent failures (invalid JSON)
  Decision: continue = false, stopReason = "5 files have syntax errors. Retrying won't help."

Agent sees:
  "5 files have JSON syntax errors. Agent halts."
  Can report which files, user fixes them
```

## Notes & links

- **PostToolBatch timing:** Fires after ALL calls in a batch resolve (or are cancelled), before Claude makes the next model call. This is the right point to decide whether to continue.
- **Distinguish from retry strategy:** PostToolBatch is about recognizing when retry is futile, not about implementing retry logic. Retry logic lives in the tool itself or in API client libraries.
- **Leverage tool error messages:** Tools that return structured error messages (via `isError: true` and detailed text) make circuit breaker logic much more reliable. See [[mcp-error-handling-model-recovery]].
- **Beware of false positives:** Pattern matching on error text is fragile. Consider logging false positive halts and refining your conditions over time.
- **Combine with budget controls:** Pair with [[cost-budgeted-routing]] to halt not just on failure patterns but also on cost/token budget exhaustion.
- **Testing:** Test your circuit breaker logic with synthetic failure cases (e.g., a tool that always fails 80% of calls) to ensure it triggers correctly.
