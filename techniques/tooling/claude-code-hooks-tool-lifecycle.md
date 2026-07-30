---
id: claude-code-hooks-tool-lifecycle
title: Claude Code Hooks for Tool Automation and Control
category: tooling
ecosystems: [claude-code]
problem: Manual tool governance is tedious; hooks automate enforcement, formatting, and safety gates without blocking workflow.
maturity: established
confidence: verified
effort_to_adopt: medium
works_with: []
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/hooks", kind: docs, date: "2026-07-28"}
  - {url: "https://claudelog.com/mechanics/hooks/", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Tool governance is manual and intrusive: you interrupt Claude to approve/deny commands, manually reformat files, or manually verify test results before merging. Hooks automate these patterns — pre-execution safety gates, post-execution formatting, and silent validation — so governance becomes invisible to the workflow.

## How it works

Claude Code hooks are shell commands, HTTP endpoints, or MCP tool calls that execute at specific points in Claude's lifecycle. Hooks receive JSON context about the event (tool name, inputs, outputs), make decisions, and control execution flow.

Two main hook types frame tool automation:
- **PreToolUse** (fires before execution, can block)
- **PostToolUse** (fires after execution, cannot undo but can reject or modify output)

Hooks live in `.claude/settings.json` (project scope) or `~/.claude/settings.json` (global scope). Exit code 0 means allow/success; exit code 2 means block/error; other codes mean continue.

## Setup

**1. Install the interactive setup**

The easiest path is Claude Code's built-in `/hooks` command:

```
/hooks
```

This walks you through selecting an event, matcher pattern, and handler.

**2. Or configure manually in .claude/settings.json**

Structure: event → matcher group → handlers:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/check-safe-commands.sh",
            "timeout": 5000
          }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/check-code-safety.sh",
            "if": "Edit(*.py)"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write",
            "timeout": 10000
          }
        ]
      }
    ]
  }
}
```

**3. PreToolUse for safety gates**

Pre-execution hooks inspect tool inputs and can block, allow, modify, or ask confirmation:

```bash
#!/bin/bash
# check-safe-commands.sh
# Block dangerous bash patterns

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command')

if [[ "$command" =~ ^(rm|dd|mkfs|chmod.*777) ]]; then
  echo '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": "Destructive command blocked: '"$command"'"
    }
  }' >&1
  exit 2
fi

exit 0
```

Input structure for PreToolUse:

```json
{
  "tool_name": "Bash",
  "tool_input": { "command": "git status" },
  "tool_use_id": "toolu_01ABC123..."
}
```

Responses can:
- **Allow**: `exit 0` (no output required)
- **Deny**: `exit 2` with `permissionDecision: "deny"`
- **Ask**: `permissionDecision: "ask"`
- **Modify**: `updatedInput` object (changes tool arguments silently)

**4. PostToolUse for formatting and verification**

Post-execution hooks can inspect results and reject operations before Claude proceeds:

```bash
#!/bin/bash
# auto-format-written-files.sh

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
file=$(echo "$input" | jq -r '.tool_input.file_path')

# Only format Python files written by Claude
if [[ "$tool_name" == "Write" && "$file" == *.py ]]; then
  npx black --quiet "$file" 2>/dev/null
fi

# Reject if tests fail
if [[ "$tool_name" == "Bash" && "$input" | jq -r '.tool_input.command' | grep -q "test" ]]; then
  output=$(echo "$input" | jq -r '.tool_response')
  if ! echo "$output" | grep -q "passed"; then
    echo '{
      "decision": "block",
      "reason": "Tests failed; fix before proceeding"
    }' >&1
    exit 2
  fi
fi

exit 0
```

Input structure for PostToolUse:

```json
{
  "tool_name": "Write",
  "tool_input": { "file_path": "/path/to/file.py", "content": "..." },
  "tool_response": "File written successfully",
  "tool_use_id": "toolu_01ABC..."
}
```

Responses can:
- **Allow**: `exit 0`
- **Block**: `decision: "block"` with reason (exit 2)
- **Provide feedback**: stderr message (Claude sees it; execution continues)
- **Replace output**: `updatedToolOutput` (Claude sees this instead)
- **Add context**: `additionalContext` (Claude receives this extra info)

**5. Matcher patterns for selective application**

Matchers determine which tools trigger the hook:

```json
{
  "matcher": "*",
  "hooks": []
}
```

Matcher syntax:
- `"*"`, `""`, or omitted = all tools
- Exact string = exact tool name (e.g., `"Bash"`)
- Pipe-separated = alternation (e.g., `"Edit|Write"`)
- Anything with other chars = JavaScript regex (e.g., `"Edit.*\\.py$"`)
- MCP tools = `mcp__<server>__<tool>` (e.g., `mcp__github__create_pull_request`)

Use `if` to filter further:

```json
{
  "matcher": "Bash",
  "if": "Bash(git *)",
  "hooks": [...]
}
```

**6. Use case: Commit message enforcement**

Enforce team conventions without blocking:

```bash
#!/bin/bash
# enforce-commit-messages.sh

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command')

if [[ "$command" =~ ^git\ commit ]]; then
  message=$(echo "$command" | grep -oP "(?<=-m\s['\"]).*?(?=['\"])" || echo "")
  
  if [[ ! "$message" =~ ^(feat|fix|refactor|docs|test|chore) ]]; then
    echo '{
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "Commit message should start with a conventional prefix (feat/fix/refactor/docs/test/chore)"
      }
    }' >&1
  fi
fi

exit 0
```

**7. Use case: Auto-format on write**

Format every file Claude writes (seamless to the workflow):

```bash
#!/bin/bash
# auto-format-all-writes.sh

input=$(cat)
file=$(echo "$input" | jq -r '.tool_input.file_path')
ext="${file##*.}"

case "$ext" in
  py) black --quiet "$file" 2>/dev/null ;;
  js|ts|tsx|jsx) npx prettier --write "$file" 2>/dev/null ;;
  md) npx prettier --write "$file" 2>/dev/null ;;
  go) gofmt -w "$file" 2>/dev/null ;;
esac

exit 0
```

## When to use / when NOT

**Use PreToolUse for:**
- Safety gates (block dangerous patterns)
- Permission enforcement (deny unsafe tool use)
- Input normalization (fix paths, add defaults)
- Secrets redaction (strip credentials before logging)

**Use PostToolUse for:**
- Auto-formatting (prettier, black, gofmt)
- Verification (test results, linting)
- Logging and audit trails
- Cleanup (temp file removal)

**Avoid:**
- Complex business logic (hooks should be thin)
- Expensive operations (keep timeouts short; 5-10 seconds typical)
- Hooks that conflict with each other (test interactions)

## Tradeoffs

- **Automation vs. transparency**: Hooks modify tool calls silently, which streamlines workflow but may surprise developers. Use clear exit codes and stderr messages.
- **Enforcement strictness**: Blocking hooks (exit 2) stop Claude; asking hooks require user input. Balance safety with autonomy.
- **Performance overhead**: Every tool call runs hooks. Keep them fast (<5s) or they slow down the workflow.

## Example

A complete hook configuration for a Python project:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "cat > /tmp/check-bash.sh << 'EOF'\n#!/bin/bash\ninput=$(cat)\ncmd=$(echo \"$input\" | jq -r '.tool_input.command')\nif [[ $cmd =~ ^(rm.*-r|dd|mkfs|chmod.*777) ]]; then\n  echo '{\"hookSpecificOutput\": {\"permissionDecision\": \"deny\"}}' >&2\n  exit 2\nfi\nexit 0\nEOF\nbash /tmp/check-bash.sh",
            "timeout": 2000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "if": "Edit|Write(*.py)",
        "hooks": [
          {
            "type": "command",
            "command": "black --quiet $(jq -r '.tool_input.file_path' <<< $0) 2>/dev/null; exit 0",
            "timeout": 5000
          }
        ]
      },
      {
        "matcher": "Bash",
        "if": "Bash(pytest.*|python -m pytest)",
        "hooks": [
          {
            "type": "command",
            "command": "# Verify tests passed\ninput=$(cat)\noutput=$(echo \"$input\" | jq -r '.tool_response')\nif ! echo \"$output\" | grep -q \"passed\"; then\n  echo '{\"decision\": \"block\", \"reason\": \"Tests failed\"}' >&2\n  exit 2\nfi\nexit 0",
            "timeout": 3000
          }
        ]
      }
    ]
  }
}
```

## Notes & links

- **Available events**: PreToolUse, PostToolUse, PostToolUseFailure, PostToolBatch, SessionStart, SessionEnd, UserPromptSubmit, Stop, PermissionRequest, etc. See the [official hooks reference](https://code.claude.com/docs/en/hooks) for the complete list.
- **Hook locations**: Global (`~/.claude/settings.json`), project (`.claude/settings.json`), or committable (`.claude/settings.local.json` for local-only rules).
- Exit code 2 is your power tool — it blocks execution and feeds stderr back to Claude, creating a feedback loop for correction.
- Hooks run with your user permissions. Treat hook scripts as executable code — review them, keep them small, avoid embedding secrets.
