---
id: pretooluse-guards-dangerous-operations
title: PreToolUse hooks to guard dangerous operations before execution
category: operations
ecosystems: [claude-code, claude-sdk]
problem: Agents invoke destructive operations (rm -rf, git push, database deletes) without safeguards; no way to block or audit before execution happens
maturity: emerging
confidence: verified
effort_to_adopt: low
works_with: [mcp-error-handling-model-recovery, schema-validation-gates]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/hooks", kind: docs, date: "2026-07-30"}
added: "2026-07-30"
updated: "2026-07-30"
---

## Problem

An agent issues `rm -rf /` or `git push --force` and only afterward do you realize the call happened. Unlike human-in-loop review (which gates after-the-fact), there is no before-the-fact guard. PreToolUse hooks fire BEFORE a tool executes, giving you a chance to block, audit, or mutate arguments.

## How it works

The PreToolUse hook intercepts each tool call before it runs. You can:
1. **Block it outright** — exit code 2 sends an error message back to Claude
2. **Inspect and decide** — return JSON with `permissionDecision` (allow / deny / ask / defer)
3. **Mutate arguments** — rewrite the input before execution (e.g., strip the `--force` flag)

The hook receives `tool_name`, `tool_input`, and `tool_use_id`. If the hook says no, Claude sees the error and can try a different approach. If it says yes, the call proceeds normally.

## Setup

**1. Create a hook script in `.claude/hooks/`**

```bash
#!/bin/bash
# .claude/hooks/block-destructive.sh
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Block rm, git push --force, and database drops
if echo "$command" | grep -qE '^\s*rm\s+(-rf|-f|--force)|git\s+push.*--force|DROP\s+(TABLE|DATABASE)'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Destructive command blocked. This operation requires explicit approval."
    }
  }'
else
  exit 0  # no decision; normal permission flow applies
fi
```

**2. Register the hook in `.claude/settings.json`**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(rm *)",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-destructive.sh",
            "args": []
          }
        ]
      }
    ]
  }
}
```

The `matcher` filters to specific tools (`Bash`, `Edit`, `Bash|Edit`, or regex patterns like `mcp__memory__.*`). The `if` pattern further narrows: `Bash(rm *)` runs the hook only when Bash is called with `rm` in the command.

**3. For dynamic decisions (ask/defer), return JSON:**

```bash
#!/bin/bash
# Hook that asks for approval on git pushes
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

if echo "$command" | grep -q 'git push'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: "git push command requires user confirmation"
    }
  }'
else
  exit 0
fi
```

**4. Halt the entire agentic loop if needed:**

For critical failures, stop Claude from making any more tool calls:

```bash
#!/bin/bash
# Critical guard: if something is very wrong, stop the agent completely
jq -n '{
  continue: false,
  stopReason: "Critical operation blocked. Agent halted to prevent damage."
}'
```

## When to use / when NOT

**Use PreToolUse guards when:**
- Operation is destructive and irreversible (rm, git push, database deletes)
- Operation requires audit trail (any sensitive command)
- Operation should never happen unattended (deploy, production writes)
- You want to block before checking permissions (preemptive defense)

**Use human-in-loop review instead when:**
- Decision is architectural and needs judgment
- Operation is reversible (file edits, tests)
- The cost of rejecting is high (don't want to block all refactors)

**Combine both when:**
- Operation is destructive AND requires architecture review
  - PreToolUse blocks bad syntax or patterns
  - Human review approves the intent

## Tradeoffs

**Wins:** Blocks bad operations before they execute, provides audit trail, prevents accidental damage, no post-facto cleanup needed.

**Costs:** Hook logic must be correct (a bug in the hook can block valid operations), hook runs on every tool call (performance), pattern matching is best-effort (some complex commands may not match).

**Important caveat:** Hook `if` patterns deliberately fail open — if your hook can't parse a command, it runs anyway. Use this only as a first layer; rely on the permission system for hard enforcement.

## Example

```
Scenario 1: Agent tries to delete with rm
  Agent: "Clean up old build artifacts" → calls Bash(rm -rf build/)
  Hook: Matches "rm *" pattern → runs block-destructive.sh
  Script: Detects "rm -rf" → returns permissionDecision: deny
  Result: Claude sees error "Destructive command blocked"
           Agent reads error and proposes alternative: mv build/ to backup folder

Scenario 2: Agent pushes to main
  Agent: "Merge the feature" → calls Bash(git push origin main)
  Hook: Matches "git push *" → runs block-destructive.sh
  Script: Detects "git push" → returns permissionDecision: ask
  Result: User is prompted: approve this push?
          User approves → push proceeds
          User denies → Claude sees error and offers to create a PR instead

Scenario 3: Normal command passes through
  Agent: "Run tests" → calls Bash(npm test)
  Hook: Matches "Bash(rm *)"? No. Pattern doesn't match.
  Result: Hook exits 0 (no decision) → normal permission flow applies
          If allowed by permissions, command runs normally
```

## Notes & links

- **Hook types:** PreToolUse supports all five handler types — `command` (shell script), `http`, `mcp_tool`, `prompt`, and `agent`. Shell scripts are simplest for pattern matching.
- **Complementary guards:** Use PreToolUse for automatic blocking, human-in-loop for architectural judgment, and schema-validation-gates for malformed inputs.
- **PostToolUse for audit:** After execution, use PostToolUse to log what ran, redact sensitive output, or validate results.
- **PostToolBatch for circuit breaking:** After a batch of parallel calls, use PostToolBatch to detect if too many failed and halt the loop.
- The `continue: false` field stops the agentic loop even if a single tool call succeeds — useful as an emergency stop.
- **Security note:** hooks run locally (not in a sandbox), so a hook script bug could expose your system. Keep hooks simple and reviewable.
