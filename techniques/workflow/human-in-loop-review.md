---
id: human-in-loop-review
title: Strategic human-in-the-loop review gates
category: workflow
ecosystems: [claude-code, claude-sdk, claude-api, generic]
problem: Too few gates = unsafe agent autonomy; too many gates = bottleneck that defeats the point
maturity: established
confidence: reported
effort_to_adopt: medium
works_with: [plan-then-execute, checkpoint-commit-discipline]
supersedes: []
sources:
  - {url: "https://explainx.ai/blog/human-in-the-loop-ai-when-to-let-agent-run-2026", kind: blog, date: "2026-07-28"}
  - {url: "https://www.port.io/blog/human-in-the-loop-for-ai-coding-agents", kind: blog, date: "2026-07-28"}
  - {url: "https://www.augmentcode.com/guides/reviewing-ai-generated-code", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Reviewing every line an agent writes doesn't scale. Agents can write 1000 lines in minutes; humans read at ~400 lines/review before effectiveness collapses. Skipping review entirely risks shipping bugs. The question isn't "should humans review?" but "which decisions should require human approval?"

## How it works

Place review gates at **architecturally critical or irreversible points**, not everywhere. Let mechanical gates (tests, linters, type checks) catch the low-hanging fruit. Reserve human judgment for decisions that:
- Cannot be undone (shipping, deleting, publishing)
- Are architectural (data model, schema, API design)
- Have security implications
- Require domain expertise

Gates fall on a spectrum:
- **Mechanical gate** (fastest): Code must pass tests, type checks, security scan before anything downstream can use it
- **Human approval before irreversible action**: Agent proposes, human approves before merge/ship
- **Human review post-facto**: For low-risk reversible changes, human reviews after agent completes (suitable for refactoring, documentation)

## Setup

1. **Define gate rules (Rule-based gates):**
   ```
   Rule 1: Any change to data model, schema, or API contract → requires architect review
   Rule 2: Any change to auth/security code → requires security review
   Rule 3: Any shell command or package install → requires human approval
   Rule 4: All other changes → must pass automated tests + linting + type checks
   ```

2. **Implement mechanical gates in CI/CD:**
   ```yaml
   # .github/workflows/agent-pr.yml
   on: [pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - run: pytest
         - run: mypy
         - run: black --check
         - run: bandit -r . # security scan
   ```

3. **Route high-risk changes to humans:**
   ```
   If (file in ["schema.sql", "auth.py", "api/routes.py"]) then require_review()
   Else if (tests all pass) then allow_merge()
   ```

4. **Use automated tools to catch issues first:**
   - Compiler/type checker catches type mismatches before humans see it
   - Test suite gives fast feedback (agent learns faster with immediate errors)
   - Linting catches style drift
   - Security scanner flags known CVEs

5. **Escalate by risk score (optional, advanced):** Instead of static rules, have a risk-scoring agent classify each change. High-risk changes pull in a human, low-risk skip review. Requires more setup but scales better.

## When to use / when NOT

**Use mechanical gates always.** They're fast and catch real bugs.

**Use human gates when:**
- Decision is architectural or data-model-level
- Security is involved
- Change is irreversible
- Domain expertise is required
- Team wants audit trail for compliance

**Avoid human gates when:**
- Change is reversible (refactoring, tests, docs)
- Mechanical checks already caught issues
- Gate becomes a bottleneck (queue grows)

## Tradeoffs

**Wins:** Catches bugs before humans see them, scales agent output, human time used strategically, clear audit trail.

**Costs:** Setup overhead (CI/CD config), risk-based gates are complex, potential for under-gating (risky changes slip through).

## Example

```
Scenario: Agent refactoring code

Agent: "I'll extract this method and add tests"
  → Runs tests (all pass)
  → Runs type checks (pass)
  → Runs security scan (pass)
  → Gate: No rules triggered → Auto-merge

Scenario: Agent adding a new API endpoint

Agent: "I'll add /users/:id/profile endpoint"
  → Runs tests (fail) → Agent fixes
  → Runs tests (pass)
  → Runs type checks (pass)
  → Gate: File is api/routes.py → Route to architect review
  → Human: Reviews architecture, approves
  → Merges

Scenario: Agent installing a package

Agent: "I'll add requests library"
  → Shell command detected
  → Gate: Package changes require approval
  → Blocks until human reviews (checks for known vulns, supply chain risk)
  → Human approves
  → Proceeds
```

## Notes & links

- **Scaling insight:** When agents write faster than humans review, the review queue becomes the bottleneck. Gate placement is how you avoid this—let mechanical gates handle volume, reserve humans for architecture.
- **Security guardrail:** Lockfile pinning and package hash verification should be automated and enforced—AI agents with package management must not install without review
- **Inverse of traditional review:** In the old model, humans reviewed everything. In the agent era, humans review exceptions. This inverts the question: what *doesn't* need review?
- **Test-driven gates improve code quality:** Agents with immediate, clear feedback loops (test fails → agent reads error → fixes → reruns → passes) produce better code than agents that wait for human review
