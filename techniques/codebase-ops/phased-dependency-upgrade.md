---
id: phased-dependency-upgrade
title: Phased Dependency Upgrades Across Large Codebases
category: codebase-ops
ecosystems: [claude-code, claude-sdk]
problem: Major dependency upgrades cause cascading failures; undisciplined agent upgrades break production
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [hybrid-codemod-agent-refactoring]
supersedes: []
sources:
  - {url: "https://medium.com/@mchathuranga4/use-of-claude-code-agents-in-mitigating-application-vulnerabilities-6c9371e19ee0", kind: blog, date: "2026-07-28"}
  - {url: "https://koder.ai/blog/claude-code-dependency-upgrades-plan", kind: blog, date: "2026-07-28"}
  - {url: "https://recombobulate.dev/tips/ask-claude-to-upgrade-a-dependency-and-fix-every-breaking-change-across-your-codebase", kind: blog, date: "2026-07-28"}
  - {url: "https://arxiv.org/html/2510.03480v2", kind: paper, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Dependency upgrades are maintenance burden disguised as simple version bumps. Changelogs rarely tell you how *your* app will fail. Finding every call site, applying the right replacement, and proving nothing broke is the real work. A "quick" upgrade becomes weeks of whack-a-mole. At scale, coordinating changes across thousands of files is impractical without automation.

## How it works

Phased upgrades break the migration into controllable chunks with safety gates between each. The agent reads the changelog, understands breaking changes, searches the codebase for affected patterns, applies fixes (via codemods or targeted edits), runs tests, and rolls back on failure. Each phase targets one category of breaking changes before moving to the next.

**Phase structure:**
1. **Planning:** Agent reads changelog, identifies breaking changes, prioritizes by risk
2. **Localization:** Find all call sites via code search (Grep/Glob)
3. **Codemods:** Apply deterministic fixes (renames, API changes, refactors)
4. **Testing:** Run full test suite; failures trigger rollback or manual review list
5. **Validation:** Re-run dependency check to ensure all transitive deps resolved
6. **Report:** Summary of changes, manual review items, version deltas

## Setup

**Agentic upgrade loop (pseudo-code):**
```
For each major breaking change in changelog:
  1. Search codebase for deprecated pattern (grep, AST search)
  2. If found, generate fix strategy (inline edit vs codemod)
  3. Apply fix to all affected files
  4. Run tests; if fails, add to manual review list
  5. Re-check dependency tree for transitive fixes
```

**In practice (dependency version bump + fix):**
```bash
# Agent bumps version in package.json or pom.xml
npm install @lib/pkg@next
# or
mvn versions:set -DnewVersion=X.Y.Z

# Agent finds breaking changes and applies codemods/edits
# (e.g., rename oldAPI -> newAPI across codebase)

# Run tests
npm test
# If fails: rollback or hand to manual review

# Re-check dependencies
npm ls @lib/pkg
```

**Language-specific patterns:**
- **JavaScript/TypeScript:** `npm outdated`, analyze package.json, run codemods for API renames
- **Java/Maven:** `mvn dependency:tree`, read pom.xml, run `mvn compile` for each phase
- **Python:** `pip list --outdated`, analyze requirements.txt, run pyupgrade or custom AST transforms

**Conservative version strategy:**
- Patch/minor upgrades: Use automated tools (Dependabot/Renovate)
- Major upgrades: Use agent + phased approach with dedicated branch and CI
- Never upgrade to major version unless current major has no fix available

## When to use / when NOT

**Use when:**
- Dependency is widely used across codebase (>20 call sites)
- Major version bump with known breaking changes
- Team needs a repeatable, auditable record of the upgrade
- Multiple transitive dependencies are affected

**Don't use when:**
- Upgrade is simple (rename, single API change affecting <5 files)
- Dependency is isolated (used in one place)
- Changelog is vague or breaking changes are unclear

## Tradeoffs

**Pros:**
- Systematic, phased approach reduces risk of cascading failures
- Produces an audit trail of every change
- Codemods minimize token cost for deterministic changes
- Failures are caught early (per-phase testing)
- Rollback is simple (git diff per phase)

**Cons:**
- Upfront planning overhead (read changelog, map call sites)
- Per-phase testing adds latency
- Codemods need language-specific tooling
- Some edge cases still require human judgment

## Example

**Scenario:** Upgrade React 17 → 18 across a large app.

**Phase 1 - API Changes:**
- Agent reads React 18 migration guide
- Identifies deprecated methods (ReactDOM.render, StrictMode, etc.)
- Generates codemod: old ReactDOM.render → new createRoot API
- Runs codemod across src/
- Runs tests: `npm test`

**Phase 2 - Hooks Changes:**
- Upgrade useEffect behavior (dependency handling)
- Agent finds all useEffect calls
- Updates dependency arrays per new rules
- Runs tests again

**Phase 3 - Validation:**
- `npm outdated` → check React and transitive deps
- `npm test` again (full suite)
- `git diff --stat` → review all changes
- Merge to main with PR

**Result:** Clean, phase-by-phase upgrade visible in git history, each phase tested before next begins.

**Multi-module Java example:**
```
Phase 1: Update pom.xml version for main library
Phase 2: mvn compile → collect errors, fix via codemods
Phase 3: Run module-level tests, build in dependency order
Phase 4: Run integration tests, verify transitive fixes
Phase 5: Report CVE fixes, version deltas, manual review list
```

## Notes & links

- **Meta-RAG technique:** For very large codebases, summarize code into structured natural language before edits; reduces token usage by ~80% by enabling efficient code localization
- **Conservative defaults:** Prefer patch/minor upgrades via bots; save agent effort for strategic major upgrades
- **Codemods are reusable:** Once you've written a codemod for an upgrade, version control it for future team members or multi-repo upgrades
- **Research:** Multi-agent LLM systems using iterative code summarization + sequential bug-fixing improve reliability on large-scale upgrades
