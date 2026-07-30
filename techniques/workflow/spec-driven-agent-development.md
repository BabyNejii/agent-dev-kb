---
id: spec-driven-agent-development
title: Spec-driven development with agent coding
category: workflow
ecosystems: [claude-code, claude-sdk, claude-api, generic]
problem: Agents without a spec drift into scope creep, build the wrong thing, or make incompatible changes
maturity: emerging
confidence: reported
effort_to_adopt: low
works_with: [plan-then-execute, ai-assisted-tdd, human-in-loop-review]
supersedes: []
sources:
  - {url: "https://www.openhands.dev/blog/claude-code-best-practices-agentic-coding", kind: blog, date: "2026-07-28"}
  - {url: "https://dev.to/ljhao/5-agent-design-patterns-every-developer-needs-to-know-in-2026-17d8", kind: blog, date: "2026-07-28"}
  - {url: "https://smart-webtech.com/blog/claude-code-workflows-and-best-practices/", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Vague directives like "improve the API" produce unpredictable results. Agents make assumptions, add features you didn't want, and sometimes change APIs in incompatible ways. A spec forces clarity on both sides: you write down exactly what should change and what shouldn't, the agent implements that spec, and nothing more.

## How it works

Write a detailed specification before coding. The spec contains:
- **What changes:** Which functions, endpoints, config, or files
- **What doesn't change:** APIs, contracts, interfaces that must stay stable
- **Edge cases:** What happens on error, with invalid input, with missing data
- **Acceptance criteria:** How to know it's done (tests to pass, metrics to meet)

The agent then codes to spec without deviation. This is different from a casual task description—it's a contract.

## Setup

1. **Write the spec (use a template):**
   ```
   Spec: Add JWT refresh token support
   
   Scope:
   ✓ Add refresh_token field to JWT response
   ✓ Add /auth/refresh endpoint
   ✓ Validate refresh_token on use
   ✗ Do NOT change /auth/login signature
   ✗ Do NOT modify existing token expiry
   
   Input/Output:
   POST /auth/refresh
   Input: {"refresh_token": "..."}
   Output: {"access_token": "...", "expires_in": 3600}
   Error: {"error": "invalid_token"} (401)
   
   Edge cases:
   - Refresh token expired → 401 error
   - Refresh token revoked → 401 error
   - Invalid signature → 401 error
   
   Acceptance:
   - All existing /auth/login tests still pass
   - New endpoint has 100% test coverage
   - Endpoint is rate-limited (max 5 per minute per user)
   ```

2. **Share spec with agent:**
   ```
   Agent task: "Implement this spec exactly:
   [paste spec]
   
   Before starting, list any assumptions you need clarified.
   Then implement, test, and commit."
   ```

3. **Agent clarifies if needed:** If spec is ambiguous, agent asks before coding.

4. **Agent codes to spec:** Implements only what's in scope, skips nice-to-haves.

5. **Verify acceptance criteria:** Agent checks each criterion before declaring done.

## When to use / when NOT

**Use when:**
- Feature has clear boundaries (most API work, library functions)
- Risk of scope creep is high
- Multiple people need to stay in sync
- You need to change existing APIs safely

**Skip when:**
- Task is exploratory ("figure out how to do X")
- You're iterating on an unclear idea
- Requirements change frequently

## Tradeoffs

**Wins:** No surprises, agent doesn't waste time on scope creep, easy to measure "done", clear audit trail of what changed.

**Costs:** Spec writing takes time, tight scope can feel restrictive, changing mid-task requires a spec update.

## Example

```
User writes spec:

Spec: Add admin role and permission system

Scope:
✓ Add Role enum: admin, user, viewer
✓ Add roles table to database schema
✓ Add middleware to check user.role before endpoint execution
✓ Update user model to include role
✗ Do NOT implement a UI for role management (future work)
✗ Do NOT change existing endpoint signatures

Database changes:
  CREATE TABLE roles (id INT PRIMARY KEY, name VARCHAR(50) UNIQUE)
  ALTER TABLE users ADD role_id INT REFERENCES roles(id)

API changes:
  GET /admin/users → only accessible if user.role == 'admin'
  GET /users/:id → accessible if user.role in ['admin', 'viewer']
  POST /users/:id → only accessible if user.role == 'admin'

Acceptance:
  - All existing tests still pass
  - New middleware has 100% test coverage
  - Schema migration is reversible
  - No breaking changes to existing endpoints

Agent implements:
  1. Modifies database schema (with migration)
  2. Adds Role enum and database model
  3. Adds middleware to check roles
  4. Updates user model
  5. Adds tests for middleware
  6. All tests pass
  7. Commits with message: "feat: add role-based access control"

No UI code, no API changes, scope preserved.
```

## Notes & links

- **Spec maturity:** A good spec prevents 80% of surprises. The remaining 20% usually require clarification, which is OK—agent asks.
- **Integration with planning:** Spec-driven development + Plan-then-Execute = controlled agent workflows
- **Scope management:** The most powerful part of specs is the "✗ Do NOT" section—it tells the agent what not to touch
- **Comparison:** This is different from TDD (where tests are the spec) but complementary—a spec can be tested, and tests can validate a spec
