---
id: controlled-dead-code-removal
title: Controlled Dead Code Removal with Language-Specific Linters
category: codebase-ops
ecosystems: [claude-code, claude-sdk, generic]
problem: Dead code accumulates; removing it without false positives requires careful tooling and verification
maturity: emerging
confidence: reported
effort_to_adopt: low
works_with: []
supersedes: []
sources:
  - {url: "https://github.com/rohitg00/awesome-claude-code-toolkit/blob/main/commands/refactoring/dead-code.md", kind: github, date: "2026-07-28"}
  - {url: "https://github.com/affaan-m/everything-claude-code/blob/main/agents/refactor-cleaner.md", kind: github, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Dead code hides in plain sight: unused imports, unreachable code blocks, functions never called, commented-out sections. Manual removal is tedious and risky (false positives: code used via dynamic imports or reflection). Automated tools (linters, static analyzers) find dead code well, but they require domain knowledge and verification to avoid removing legitimate code.

## How it works

Use language-specific linters to *detect* dead code, then have the agent *verify* it's safe before removal. Batch the removals in small groups, run the full test suite after each batch, and maintain a manual-review list for ambiguous cases (string references, reflection, public APIs).

**Detection tools by language:**
- **JavaScript/TypeScript:** ESLint (no-unused-vars), tsc (--noUnusedLocals), typescript-unused-exports
- **Python:** ruff (F401), flake8 (--select=F401), vulture, pyflakes
- **Java:** IntelliJ IDEA analysis, SpotBugs, Checker Framework
- **Go:** go vet (unused), staticcheck
- **Rust:** clippy, compiler warnings (#[warn(dead_code)])

**Removal strategy:**
1. Run linter to detect candidates
2. Group by confidence (high confidence: truly unused; low: might be dynamic)
3. Agent removes high-confidence batch
4. Run full test suite
5. If tests pass: commit; if fail: investigate false positive, add to manual review list
6. Repeat for next batch

## Setup

**Scan for dead code (examples by language):**

**JavaScript/TypeScript:**
```bash
# Detect unused variables
npx eslint --rule 'no-unused-vars: error' src/

# Detect unused imports
npx eslint --rule 'no-unused-imports: error' src/

# TypeScript: find unused exported symbols
npx tsc --noUnusedLocals --noUnusedParameters --noEmit

# Find unused exports
npx ts-prune src/
```

**Python:**
```bash
# Find unused imports
ruff check --select F401 src/

# Find dead code and unused functions
vulture src/

# Flake8 for unused variables
flake8 --select=F401 src/
```

**Java/Maven:**
```bash
# IntelliJ IDEA inspection (command-line)
# or use SpotBugs for dead code analysis
mvn spotbugs:spotbugs

# Check for unused classes/methods
mvn org.jmarc:maven-dead-code-detector-plugin:analyze
```

**Agentic removal loop:**
```
1. Run linter and collect dead code candidates
2. Filter by confidence:
   HIGH: unused local variables, unreachable code, never-exported functions
   LOW: public API exports, string-referenced code, reflection targets
3. Review and approve HIGH confidence list with human
4. Agent removes HIGH confidence batch
5. Run full test suite (npm test, pytest, mvn test, etc.)
6. If all pass: commit
7. If any fail: investigate (false positive?), add to manual review
8. Repeat for next batch
```

**Safety rules:**
- **Never remove** code that:
  - Is exported as part of a public API or SDK
  - May be used via string references or dynamic imports
  - Is used by tests (test utilities, fixtures)
  - Is marked as development-only but intentionally kept
  - Has comments explaining why it's kept around

- **Always verify** by:
  - Running the full test suite after each batch
  - Checking for grep-detectable string references before removal
  - Reviewing git diff before commit

## When to use / when NOT

**Use when:**
- Codebase is large and has accumulated debt
- Tests are comprehensive (coverage >70%)
- Linters are well-configured for the project
- Team has time for careful batch removal and testing

**Don't use when:**
- Tests are sparse (<50% coverage, flaky)
- Codebase uses heavy reflection or dynamic imports
- Code is mission-critical with risk of undetected issues
- Linters are not configured or trusted for your codebase

## Tradeoffs

**Pros:**
- Language-specific tools are reliable and well-maintained
- Batch + test approach catches false positives early
- Cleanup improves codebase maintainability
- Low effort (automated detection, agent verification)
- Safe (comprehensive testing between batches)

**Cons:**
- Requires comprehensive test coverage to verify
- Some false positives (especially dynamic/reflection code)
- Batch processing is slower than one-shot removal
- Linters must be configured correctly for accuracy

## Example

**Scenario:** Python service with 20k LOC, 65% test coverage. Goal: remove unused imports and dead functions.

**Step 1: Detect**
```bash
vulture src/ > dead-code.txt
ruff check --select F401 src/ > unused-imports.txt
```

**Step 2: Filter by confidence**
```
HIGH CONFIDENCE (agent-approved removal):
- unused_helper() in src/utils.py (never called, not exported)
- import os in src/config.py (no refs)
- dead_route() in src/api.py (commented: "legacy, replaced by new_route")

LOW CONFIDENCE (manual review):
- EventHandler.__init__ (might be called via reflection)
- utils.format_json (public API, used by customers)
- Feature flag always=False (check all feature gates first)
```

**Step 3: Remove HIGH confidence batch**
```python
# Agent removes:
# - unused_helper() from utils.py
# - "import os" from config.py
# - dead_route() from api.py
```

**Step 4: Test**
```bash
pytest -v
# All tests pass
```

**Step 5: Commit**
```bash
git add -A
git commit -m "refactor: remove dead code and unused imports

- Remove unused_helper() from utils.py
- Remove unused 'import os' from config.py
- Remove dead_route() from api.py (replaced by new_route())

All tests passing."
```

**Step 6: Repeat for next batch** (manual review items, lower confidence)

## Notes & links

- **False positives:** Code used via dynamic import (`__import__("module")`) or string methods (`.format("{value}", value=x)`) may appear unused to static tools; always check grep and tests
- **Test coverage is prerequisite:** Without comprehensive tests, dead code removal is risky; tests are your safety net
- **Public APIs:** Never remove exports from public APIs or SDKs; maintain backward compatibility or follow deprecation protocols
- **Dedicated agents exist:** The "refactor-cleaner" agent (GitHub: everything-claude-code) automates this with knip, depcheck, ts-prune for JavaScript; similar patterns exist for other languages
