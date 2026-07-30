---
id: iterative-self-refinement
title: Iterative self-refinement loops for agent code quality
category: workflow
ecosystems: [claude-code, claude-sdk, claude-api, generic]
problem: Agents produce code on first try that is correct but unmaintainable, or that misses edge cases
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [ai-assisted-tdd, checkpoint-commit-discipline, plan-then-execute]
supersedes: []
sources:
  - {url: "https://deepsense.ai/resource/self-correcting-code-generation-using-multi-step-agent/", kind: blog, date: "2026-07-28"}
  - {url: "https://addyosmani.com/blog/self-improving-agents/", kind: blog, date: "2026-07-28"}
  - {url: "https://arxiv.org/pdf/2508.07407", kind: paper, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

A single-pass generation by an agent often produces working code but with hidden issues: poor test coverage, high cyclomatic complexity, or edge cases not handled. The agent doesn't know what "better" looks like unless you feed it explicit metrics.

## How it works

Use a multi-pass loop where the agent generates code, then reviews it against measurable quality criteria, and refines:

1. **Generate:** Agent writes code to pass the functional requirements
2. **Review:** Agent evaluates code against quality metrics (test coverage, complexity, lint issues, type safety)
3. **Refine:** Agent makes targeted improvements based on the review
4. **Repeat:** Loop until metrics reach target or diminishing returns

The key is coupling the loop to **objective metrics** (coverage %, complexity score, lint count) not subjective self-critique. Agents alone are unreliable judges of their own work; metrics are not.

## Setup

1. **Establish quality targets:**
   ```
   - Test coverage: > 80%
   - Cyclomatic complexity: < 10 per function
   - Lint errors: 0
   - Type check errors: 0
   - No TODO comments
   ```

2. **Wire feedback tools:**
   ```bash
   pytest --cov=src/  # Coverage
   radon cc src/      # Complexity
   pylint src/        # Linting
   mypy src/          # Type safety
   ```

3. **Create refinement loop:**
   ```
   Agent iteration 1:
     → Write code
     → Run pytest → 45% coverage (FAIL)
   
   Agent iteration 2:
     → Review coverage report
     → Add tests for uncovered branches
     → Run pytest → 82% coverage (PASS)
     → Run radon → avg complexity 5 (PASS)
     → Run mypy → 0 errors (PASS)
     → Done
   ```

4. **Automate the loop:** Direct the agent with clear instructions:
   ```
   "Write a function to parse CSV files. 
    Then measure: coverage, complexity, linting. 
    Refine until: coverage > 80%, complexity < 8, no lint errors.
    Show me the metrics before and after each pass."
   ```

5. **Use specialized frameworks for advanced loops:**
   - **Self-Refine:** Agent generates output, critiques it in natural language, revises
   - **Self-Debug:** Agent tests its own code and fixes bugs based on test output
   - **Self-Programming AI (SPA):** Integrates pytest, coverage.py, radon, pylint and autonomously proposes AST-level improvements

## When to use / when NOT

**Use when:**
- Quality standards are high (library code, shared infrastructure)
- You can define clear metrics
- Code correctness is critical

**Skip when:**
- Prototyping or spiking (first-draft OK)
- Feature is low-criticality
- Metrics are hard to define (UI, creative output)

## Tradeoffs

**Wins:** Measurably higher quality (studies show ~54% → ~82% correctness), comprehensive coverage, safe refactoring, fewer edge cases missed.

**Costs:** Longer generation time (multiple passes), higher compute cost, metrics sometimes don't capture everything (hard to measure "is this elegant?").

## Example

```
Iteration 1:
  Agent writes: csv_parser.py
  Coverage: 45%, Complexity avg: 7, Lint: 12 errors
  
Iteration 2:
  Agent sees coverage report: function parse_row() is untested
  Adds tests for parse_row edge cases
  Coverage: 72%, Complexity avg: 7, Lint: 4 errors
  
Iteration 3:
  Agent sees lint errors: variable names, unused imports
  Cleans up: removes unused imports, renames vars
  Also sees coverage gap in error handling
  Adds error-case tests
  Coverage: 85%, Complexity avg: 6, Lint: 0
  → Done (meets targets)
```

## Notes & links

- **Key distinction:** Self-critique (agent judges itself) vs. objective metrics. Critique alone doesn't work; metrics do. Best practice: combine both.
- **Benchmark evidence:** Self-Refine framework shows multi-pass LLM generation improves both correctness and user-perceived quality
- **Cost insight:** Each pass doubles the cost and time, but the first pass→second pass jump is ~20% quality gain; second→third is ~5% gain (diminishing returns)
- **Integration:** Pair with TDD and checkpoint discipline—agents that see test failures immediately refine faster than agents that wait for batch feedback
- **Advanced pattern "Ralph Wiggum":** Break development into many small tasks, run agent in loop for each task (write → test → commit → next task)
