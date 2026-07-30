---
id: code-summary-meta-rag
title: Meta-RAG Code Summarization for Large-Scale Migrations
category: codebase-ops
ecosystems: [claude-code, claude-sdk, claude-api]
problem: Large codebases exceed context windows; agents can't reason about 1M+ LOC projects in one pass
maturity: experimental
confidence: reported
effort_to_adopt: high
works_with: [phased-dependency-upgrade, hybrid-codemod-agent-refactoring]
supersedes: []
sources:
  - {url: "https://arxiv.org/html/2510.03480v2", kind: paper, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Multi-million-line codebases don't fit in context. Even with 200k token windows, a single agent reviewing the full graph is impossible. Traditional RAG (retrieve-relevant-code) works for small lookups, but migrations need holistic understanding: change impacts spread across the tree, and missing a module breaks the entire transformation. The challenge: compress a massive codebase into something an agent can reason about, then use that summary to localize and execute precise edits.

## How it works

**Meta-RAG** is a code-summarization technique that:
1. Partitions the codebase into logical units (modules, packages, layers)
2. Summarizes each unit into structured natural language (signatures, dependencies, APIs)
3. Builds a high-level dependency graph from summaries
4. Feeds the summary + localized code to the agent for edits
5. Achieves ~80% token reduction vs. raw code

**Process:**
- **Pre-migration:** Scan codebase, extract module boundaries, generate summaries (once per project)
- **Per-edit phase:** Retrieve relevant summaries + localized source files for the specific change
- **Edit:** Agent performs surgery using summaries for context + raw code for precision
- **Iterate:** Update summaries, move to next module

## Setup

**Phase 1: Generate summaries (offline, once)**

```python
def summarize_module(module_path, files):
    """Create a structured summary of a module."""
    summary = {
        "name": module_name,
        "purpose": "2-3 sentence description",
        "public_api": [
            {"name": "function_name", "signature": "...", "purpose": "..."},
            {"name": "ClassA", "methods": [...], "purpose": "..."}
        ],
        "dependencies": {
            "external": ["pkg1==1.0", "pkg2==2.0"],
            "internal": ["../other_module", "../core"]
        },
        "key_exports": ["api", "models", "handlers"]
    }
    return summary
```

Example output:
```yaml
module: api/handlers
purpose: |
  Defines HTTP request handlers for REST API.
  Delegates to services, validates input, returns JSON.

public_api:
  - name: AuthHandler
    signature: "class AuthHandler(BaseHandler)"
    purpose: "Handles /auth/* endpoints"
    methods:
      - name: POST /login
        signature: "POST(username, password) -> {token}"
  
dependencies:
  external: [requests==2.28, jwt==1.2]
  internal: [../services, ../models, ../middleware]

key_exports: [AuthHandler, HealthHandler]
```

**Phase 2: Build dependency graph from summaries**

```
api/handlers
  ├─ depends_on: services/auth
  ├─ depends_on: models/user
  └─ depends_on: middleware/logging

services/auth
  ├─ depends_on: models/user
  ├─ depends_on: database/queries
  └─ external: [jwt==1.2, bcrypt==3.2]
```

**Phase 3: Prepare for migration**

When upgrading a dependency, agent sees:
```
TASK: Upgrade jwt 1.0 -> 2.0

IMPACT ANALYSIS (from summaries):
- api/handlers.AuthHandler calls jwt.decode() [NEEDS UPDATE]
- services/auth.TokenService calls jwt.encode() [NEEDS UPDATE]
- middleware/auth.VerifyToken calls jwt.decode() [NEEDS UPDATE]

EXECUTION PLAN:
1. Fetch summary + source for api/handlers
2. Identify jwt.decode() calls, update per v2.0 guide
3. Fetch summary + source for services/auth
4. Update jwt.encode() calls
5. Update middleware/auth
6. Run tests
```

**Phase 4: Localized edits**

```python
# Agent prompt (with summaries for context, raw code for edits)
"""
Upgrade jwt library from 1.0 to 2.0.

AVAILABLE SUMMARIES (read-only):
- api/handlers: Handles HTTP requests, calls jwt.decode()
- services/auth: Token management, calls jwt.encode()
- middleware/auth: Verifies tokens, calls jwt.decode()

LOCALIZED FILES (edit these):
- src/api/handlers.py (64 LOC)
- src/services/auth.py (128 LOC)
- src/middleware/auth.py (45 LOC)

MIGRATION GUIDE:
- jwt.decode(payload, key) -> jwt.decode(payload, key, algorithms=['HS256'])
- jwt.encode() signature unchanged

TASK:
1. Update all jwt.decode() calls to include algorithms
2. Run tests in src/tests/test_auth.py
3. Report changes
"""
```

## When to use / when NOT

**Use when:**
- Codebase exceeds 500k LOC and single-pass reasoning is infeasible
- Migration impacts many modules (>10) but is systematic
- Budget/latency constraints exist (80% token reduction is significant)
- Project is stable (summaries don't need constant refresh)

**Don't use when:**
- Codebase is small (<100k LOC; simpler to pass raw code)
- Migration is one-off or exploratory
- Code changes frequently (summaries go stale)
- Deep business logic is required per file (summaries lose nuance)

## Tradeoffs

**Pros:**
- Reduces token usage by ~80% (verified on large codebases)
- Enables reasoning over multi-million-line projects
- Structured format (APIs, dependencies) is agent-friendly
- Reusable across multiple migrations
- Scales to enterprise monoliths

**Cons:**
- Significant upfront effort to generate accurate summaries
- Summaries must be maintained (refactoring invalidates them)
- Loss of detail (business logic, edge cases) in summaries
- Agents may miss subtle dependencies not captured in summary
- Requires careful validation to ensure summary accuracy

## Example

**Scenario:** Upgrade Express 4 → 5 across a 2M LOC Node.js monolith.

**Pre-migration (one-time):**
```bash
# Generate summaries for 50+ modules
python summarize_codebase.py src/ > summaries.yaml
# Output: 50 module summaries, ~100 KB (vs. 20 MB raw code)
```

**Migration (breaking it down):**

**Summary view (agent reads):**
```yaml
api/routes: 200 LOC, exports: [userRouter, authRouter, productRouter]
  - depends_on: services/users, services/auth
  - external: [express==4.18]
```

**Raw code view (agent edits):**
```python
# src/api/routes/users.ts (120 LOC that will be edited)
```

**Agent task:**
```
Upgrade Express 4 -> 5 using Meta-RAG approach.

STEP 1: Review summaries for modules that import/use express
STEP 2: Fetch full source + summary for each affected module
STEP 3: Identify breaking changes from changelog:
   - app.use() signature change
   - middleware chaining
   - res.header -> res.set()
STEP 4: Apply fixes using raw code files
STEP 5: Verify with tests
```

**Result:** Agent handles 2M LOC by working on 50 modules × 5-10 LOC changes each, using summaries for context and raw code for precision edits.

## Notes & links

- **Research basis:** arXiv paper on LLM agents for automated dependency upgrades (2510.03480) describes Meta-RAG as an enabling technique
- **Tool support:** No standard tool yet; custom implementation per codebase
- **Maintenance cost:** Summaries must be regenerated after major refactorings (treat as infrastructure)
- **Validation:** Always run full test suite after Meta-RAG migrations; summaries can miss dynamic imports or unusual patterns
- **Integration:** Pairs well with phased upgrades (each phase uses localized summaries) and hybrid codemods (agent generates codemod, codemod edits localized files)
