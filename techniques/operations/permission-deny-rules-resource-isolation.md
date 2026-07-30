---
id: permission-deny-rules-resource-isolation
title: Permission deny rules for hard resource and capability isolation
category: operations
ecosystems: [claude-code]
problem: Agents can read any file (secrets, credentials), run any command, access any service without hard limits; difficult to sandbox untrusted or multi-tenant agents
maturity: emerging
confidence: verified
effort_to_adopt: low
works_with: [pretooluse-guards-dangerous-operations, human-in-loop-review]
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/settings", kind: docs, date: "2026-07-30"}
added: "2026-07-30"
updated: "2026-07-30"
---

## Problem

An agent asks to read `/root/.ssh/id_rsa` or `.env` and you have to trust the agent not to. There's no hard boundary: PreToolUse hooks are auditable but can be bypassed by clever input transformation; human review scales poorly. Permission deny rules are declarative, enforced by the Claude Code harness before even asking the user, and they fail closed — invalid denies are stripped with a warning while valid rules stay enforced.

## How it works

In `.claude/settings.json`, you define three buckets:
- **allow**: Tool patterns that are always permitted (e.g., `npm run test`)
- **deny**: Tool patterns that are always blocked (e.g., `Bash(curl *)`, `Read(.env)`)
- **ask**: Tool patterns that require user approval on each call (e.g., `Bash(sudo *)`)

Rules use the form `Tool(pattern)` with wildcards. The harness evaluates them before the tool runs. A denied pattern gets blocked with a user-facing message. No agent can work around it — deny rules are not negotiable.

## Setup

**1. Define deny rules in `.claude/settings.json`**

```json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(./secrets/**)",
      "Read(/root/**)",
      "Bash(curl *)",
      "Bash(sudo *)",
      "Bash(rm -rf *)",
      "Edit(.env)",
      "Edit(.env.*)"
    ]
  }
}
```

Each pattern is checked: if a tool call matches a deny rule, the call is blocked and the agent sees an error. The agent cannot proceed without you changing the rules.

**2. Add allow rules for common safe operations**

Allow rules reduce permission prompts for known-good patterns:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run test)",
      "Bash(npm run build)",
      "Bash(npm run lint)",
      "Bash(git status)",
      "Bash(git diff)",
      "Read(package.json)",
      "Read(src/**)",
      "Read(tsconfig.json)"
    ],
    "deny": [
      "Read(.env)",
      "Read(./secrets/**)",
      "Bash(curl *)",
      "Bash(rm -rf *)"
    ]
  }
}
```

Matching proceed from most specific to least specific. A call matching both allow and deny uses the first explicit match; if no match, defaults to ask the user.

**3. Project-level vs. user-level rules**

Place deny rules in `.claude/settings.json` (project-scoped, checked into repo):

```json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(./secrets/**)"
    ]
  }
}
```

Place local overrides in `.claude/settings.local.json` (user-specific, not in git):

```json
{
  "permissions": {
    "allow": [
      "Read(.env.test)"
    ]
  }
}
```

Local rules take precedence over project rules.

**4. Wildcard patterns**

Rules support `*` (any characters in a single path segment) and `**` (any characters across multiple segments):

| Pattern | Matches | Does NOT match |
|---------|---------|----------------|
| `Read(.env)` | `.env` (exactly) | `.env.local`, `.envrc` |
| `Read(.env*)` | `.env`, `.env.local`, `.env.prod` | `env.txt` |
| `Read(./secrets/**)` | `./secrets/api_key.txt`, `./secrets/db/password.txt` | `./src/secrets/key.txt` (wrong path) |
| `Bash(curl *)` | `curl example.com`, `curl -H "Auth: token"` | `git clone https://example.com` (no match) |
| `Bash(rm *)` | `rm file.txt`, `rm -rf dir` | `git rm file.txt` (different command) |

**5. Combine with ask rules for sensitive but necessary operations**

Ask rules prompt the user each time:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm install)",
      "Bash(git push)"
    ],
    "ask": [
      "Bash(npm install *)",
      "Bash(npm uninstall *)"
    ],
    "deny": [
      "Bash(sudo *)",
      "Bash(curl *)"
    ]
  }
}
```

Here, `npm install` (install from package.json) is allowed, but `npm install new-package` requires a prompt, and `sudo` is always denied.

## When to use / when NOT

**Use deny rules when:**
- Protecting secrets (.env, credentials, private keys)
- Preventing infrastructure changes (sudo, cloud CLI commands)
- Blocking exfiltration vectors (curl to external sites)
- Sandbox untrusted or multi-tenant agents
- You need a hard enforcement boundary (not just audit)

**Use ask rules when:**
- Operation is sensitive but sometimes needed (package installs)
- You want explicit approval each time (git push in prod)
- Operation is reversible but risky (rm, database deletes)

**Use allow rules to:**
- Reduce permission prompt fatigue for routine operations
- Speed up workflows by pre-approving safe patterns
- Document "these patterns are always OK"

**Do NOT use deny rules for:**
- Logic you expect agents to work around (agents are clever)
- Enforcing code quality (use linters and CI/CD instead)
- Controlling which files agents read (if you don't trust them, don't put them in the repo)

## Tradeoffs

**Wins:** Hard boundary that agent cannot bypass, fail-closed (invalid rules are stripped, valid ones stay), no performance overhead, simple to reason about, scales to any number of agents.

**Costs:** Rules are static (can't adapt to runtime conditions), require upfront enumeration of what to block (not comprehensive), pattern matching can have false positives or false negatives, can block legitimate workflows if too aggressive.

**False positives:** An overly broad deny rule like `Bash(*)` would block all shell execution. Start with deny + allow, test, then refine.

**False negatives:** An agent might call `cat .env` instead of `Read(.env)` and bypass the rule. The deny rule blocks the specific tool call, not the underlying capability.

## Example

### Project A: Scientific computing (protect data, allow experimentation)

```json
{
  "permissions": {
    "allow": [
      "Bash(python scripts/*)",
      "Bash(jupyter notebook)",
      "Read(data/public/**)",
      "Read(notebooks/**)"
    ],
    "deny": [
      "Read(data/private/**)",
      "Read(data/raw/**)",
      "Bash(curl *)",
      "Bash(ssh *)"
    ],
    "ask": [
      "Bash(rm *)",
      "Edit(scripts/*)"
    ]
  }
}
```

Agents can run Python scripts and Jupyter, read public data, but cannot access private datasets, exfiltrate via curl, or delete files without approval.

### Project B: Multi-tenant SaaS (strict isolation)

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run test)",
      "Bash(npm run build)",
      "Read(src/**)",
      "Read(package.json)"
    ],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(./config/secrets.yml)",
      "Read(./database/**)",
      "Bash(curl *)",
      "Bash(ssh *)",
      "Bash(sudo *)",
      "Bash(git push *)",
      "Edit(.env)"
    ]
  }
}
```

Each tenant's agent can build and test but cannot access credentials, databases, or push code. All infrastructure and deployment is human-controlled.

### Project C: Internal helper (low trust)

```json
{
  "permissions": {
    "allow": [
      "Read(README.md)",
      "Read(docs/**)"
    ],
    "deny": [
      "Bash(*)",
      "Edit(*)",
      "Write(*)",
      "Read(.env)"
    ]
  }
}
```

Agent can only read documentation. Everything else is blocked.

## Notes & links

- **Scope hierarchy:** Rules in `settings.local.json` override project `settings.json`, which overrides user `~/.claude/settings.json`. Managed rules (organization-level) always take precedence.
- **Fail-closed behavior:** Invalid deny rules are stripped with a warning, but the valid rules stay enforced. This is a security design: a typo cannot accidentally enable a blocked operation.
- **Permissions are live:** Changes to `.claude/settings.json` take effect immediately without restarting; no caching.
- **Combine with hooks:** Deny rules are the first layer (hard boundary); PreToolUse hooks are the second layer (fine-grained audit/block). Use both.
- **Audit and logging:** Denied calls are logged in the transcript so you can see what the agent tried to do and why it was blocked.
- **Workspace trust:** Allow rules in `.claude/settings.json` (repo-checked) require a one-time workspace trust step. Allow rules in `.claude/settings.local.json` (user-only) apply immediately.
- **Troubleshooting:** Run `claude /status` to see the current effective permission rules and their sources.
