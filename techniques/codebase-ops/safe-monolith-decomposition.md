---
id: safe-monolith-decomposition
title: Structured Workflow for Safe Monolith Decomposition
category: codebase-ops
ecosystems: [claude-code, claude-sdk]
problem: Decomposing monoliths is high-risk; undisciplined refactoring causes hidden breakages
maturity: emerging
confidence: reported
effort_to_adopt: high
works_with: []
supersedes: []
sources:
  - {url: "https://www.sitepoint.com/claude-code-refactoring-workflow/", kind: blog, date: "2026-07-28"}
  - {url: "https://github.com/rohitg00/awesome-claude-code-toolkit/blob/main/commands/refactoring/dead-code.md", kind: github, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Monoliths don't decompose incrementally without structure. An unconstrained "refactor this" prompt lets Claude rewrite files, update imports, rename exports, and chain destructive changes before the developer even understands the dependency graph. The result: tangled refactorings that touch unrelated code, introduce subtle breakages, and are impossible to review.

## How it works

The **analysis-first, verification-between-steps** workflow separates the dangerous phases. First, the agent reads everything and maps dependencies *without* modifying files. Only after human review of the plan does execution begin, one step at a time, with tests between each step.

**Structured phases:**
1. **Scope Definition:** Declare in-scope and read-only files via CLAUDE.md; set session rules
2. **Analysis:** Agent reads all target files, discovers dependencies, outputs a dependency graph
3. **Planning:** Agent proposes a step-by-step refactoring plan (exact file changes, imports, exports)
4. **Human Review:** Developer reviews and approves the plan before any code changes
5. **Execution:** Apply changes one step at a time; test after each step
6. **Cleanup:** Sweep for orphaned imports, dead code, and unused variables
7. **Review:** Submit PR with clean commit history

## Setup

**Step 1: Create CLAUDE.md with scope:**
```markdown
# Refactoring Rules

## In Scope
- src/api/routes/ (target for decomposition)
- src/api/middleware/ (may need updates)
- tests/ (test files)

## Read-Only
- src/core/ (no changes allowed)
- src/database/ (no changes allowed)

## Constraints
- No renaming exports unless explicitly approved
- Each commit must pass tests
- PR title must include "refactor: "
```

**Step 2: Branch and analyze:**
```bash
git checkout -b refactor/decompose-api-routes
```

**Agentic prompt (analysis only):**
```
1. Read all files in src/api/routes/ and src/api/middleware/
2. For each file, map:
   - All exports
   - All imports (internal and external)
   - Which files depend on this file
   - Function/class signatures
3. Output a dependency graph as a table
4. DO NOT MODIFY ANY FILES
```

**Verify analysis:**
```bash
git diff --name-only  # Should be empty
```

**Step 3: Review and approve the plan:**

Agent outputs a structured refactoring plan:
```
STEP 1: Create new file src/api/routes/auth-routes.ts
  - Extract: loginHandler, logoutHandler from routes/index.ts
  - Exports: { loginHandler, logoutHandler }

STEP 2: Update src/api/routes/index.ts
  - Import { loginHandler, logoutHandler } from ./auth-routes
  - Remove old handler definitions
  - Update re-exports

STEP 3: Run tests
  - npm test -- src/api/routes/

STEP 4: Create src/api/routes/user-routes.ts
  ...
```

**Human reviews** and approves before execution.

**Step 4: Execute step-by-step:**
```bash
# Step 1: Create auth-routes.ts
# (Agent creates the file with extracted functions)

git diff src/api/routes/auth-routes.ts
# Review the new file
git add src/api/routes/auth-routes.ts
git commit -m "refactor: extract auth handlers to separate module"

# Step 2: Update routes/index.ts
# (Agent updates imports and removes old code)

git diff src/api/routes/index.ts
# Review imports and re-exports
npm test -- src/api/routes/
# Ensure tests pass before moving on

git add src/api/routes/index.ts
git commit -m "refactor: import auth handlers from new module"

# Repeat for each step
```

**Step 5: Cleanup:**
```
Prompt: Sweep all changed files for:
- Orphaned imports
- Unused variables
- Dead code (code after return/throw statements)
- Feature flags that are always true/false

Use: tsc --noUnusedLocals, ESLint no-unused-vars, etc.
```

**Step 6: Final validation:**
```bash
npm test
git log --oneline refactor/decompose-api-routes
# Review commit history — each should be atomic and testable
```

## When to use / when NOT

**Use when:**
- Monolith is large and interdependent (>5k LOC with complex imports)
- Team needs an audit trail (regulatory, complex business logic)
- Changes affect multiple modules and carry risk
- Developers need to understand each step before approval

**Don't use when:**
- Refactoring is simple and local (<3 files, isolated changes)
- Codebase is small enough to reason about holistically
- Tests are sparse (high risk of undetected breakages)

## Tradeoffs

**Pros:**
- Analysis without modification ensures safe exploration
- Step-by-step execution enables early detection of issues
- Commits are atomic and reviewable
- Dependency graph is explicit and auditable
- Reduces risk of cascading failures or hidden breakages

**Cons:**
- Longer overall duration (analysis → review → execution → verification)
- Requires multiple human review cycles
- Agent spawning overhead (per-step prompts)
- Not suitable for rapid iteration (structured, but slower)

## Example

**Scenario:** Decompose Express.js monolith route handler into separate route modules.

**Starting state:** `src/index.ts` contains 500 LOC with all routes inline.

**After phase 1 (analysis):**
Agent outputs dependency map:
```
GET /auth/login  → authMiddleware → database.getUser → logger
GET /auth/logout → sessionMiddleware
GET /users/:id   → authMiddleware → database.getUser
POST /users      → authMiddleware → database.create → mailer
```

**Refactoring plan (human-approved):**
1. Extract auth routes to `src/routes/auth.ts`
2. Extract user routes to `src/routes/users.ts`
3. Update `src/index.ts` to import and register routes
4. Update tests
5. Verify no dead imports

**Execution (4 commits):**
```
refactor: extract auth routes to separate module
refactor: extract user routes to separate module
refactor: register routes from new modules
refactor: remove dead code and unused imports
```

## Notes & links

- **Danger pattern:** Unconstrained "refactor this entire file" → agent rewrites file, updates imports everywhere, renames exports, all in one action before review
- **Safety pattern:** Read-only → analysis → human review → execute one step → test → repeat
- **Tool support:** Use language-specific linters (tsc, ESLint, mypy) in cleanup phase to catch orphaned code
- **Monolith decomposition is a refactoring, not a rewrite:** Structure matters more than speed
