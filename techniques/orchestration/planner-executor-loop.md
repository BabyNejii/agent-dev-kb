---
id: planner-executor-loop
title: Planner-executor loop for iterative code generation
category: orchestration
ecosystems: [claude-code, claude-sdk, generic]
problem: Large code-generation tasks fail when agent tries to write and test in a single pass; need separate planning and execution phases.
maturity: established
confidence: reported
effort_to_adopt: medium
works_with: [supervisor-pattern]
supersedes: []
sources:
  - {url: "https://www.emergentmind.com/topics/planner-executor-architecture-4c9e0097-fe2b-4870-b41c-9519c49a07c8", kind: blog, date: 2026-07-28}
  - {url: "https://productschool.com/blog/artificial-intelligence/ai-agent-orchestration-patterns", kind: blog, date: 2026-07-28}
  - {url: "https://arxiv.org/pdf/2509.07595", kind: paper, date: 2026-07-28}
  - {url: "https://medium.com/@vishal.agarwal.iitk/agent-architectures-planner-executor-router-patterns-148fe54ff595", kind: blog, date: 2026-07-28}
added: 2026-07-28
updated: 2026-07-28
---

## Problem

A single agent trying to design *and* implement *and* test a large system in one pass produces low-quality code. The agent holds design decisions while implementing, then abandons them when testing fails. Context window fills with debugging noise.

## How it works

Separate agents for planning and execution:

1. **Planner** decomposes the entire task into a detailed step-by-step plan.
   - Reads spec/requirements.
   - Outputs a sequence of high-level tasks (design database schema, implement API routes, write tests, etc.).
   - Each task is self-contained and manageable.

2. **Executor** implements one step at a time.
   - Reads the plan step.
   - Writes code or runs tests for that step only.
   - Reports success/failure and any blockers back.
   - Executor can be simpler/cheaper than planner (smaller model, or deterministic code mapper).

3. **Evaluator** (optional) validates each step.
   - Runs tests against executor's output.
   - Sends feedback back to planner if a step failed.
   - Planner optionally revises plan or escalates.

## Setup

```python
# Planner decomposes
planner_agent = Agent(
    name="planner",
    prompt="Break this task into a sequence of concrete implementation steps. Each step should be 1-3 sentences and independently testable."
)
plan = planner_agent.run(user_request)

# Executor runs steps iteratively
executor_agent = Agent(
    name="executor",
    prompt="Implement exactly this one step from the plan. Do not skip to later steps."
)

evaluator_agent = Agent(
    name="evaluator",
    prompt="Test the code. Report pass/fail and any errors."
)

results = []
for step in plan.steps:
    code = executor_agent.run(step)
    test_result = evaluator_agent.run(code)
    results.append({step: code, test: test_result})
    
    if test_result.failed:
        # Replan or debug
        plan = planner_agent.run(f"Previous step failed: {test_result.error}. Adjust plan.")
```

## When to use / when NOT

- **USE** for code generation tasks >100 lines or >3 logical components.
- **USE** when you want to separate concerns (design from implementation from validation).
- **USE** for iterative refinement loops (planner adjusts if executor fails).
- **NOT** for simple one-function tasks (overhead not worth it).
- **NOT** when design and implementation are tightly coupled (e.g., microoptimization needs global context).

## Tradeoffs

- **Cost:** Two or three agents + loop overhead. More expensive than single-agent.
- **Latency:** Each step waits on executor completion before moving to next. Not as parallelizable as [[supervisor-pattern]].
- **Quality:** Cleaner separation of concerns. Executor focuses on one task. Easier to debug failures per step.
- **Flexibility:** If a step fails, you can replan or retry without restarting from the beginning.

## Example

Generating a web scraper:
1. **Planner:** "Steps: 1) Define target URLs and CSS selectors. 2) Implement page fetcher with retry logic. 3) Implement parser for each page type. 4) Write tests for each parser. 5) Integrate into main loop."
2. **Executor step 1:** Outputs selectors and URL list.
3. **Executor step 2:** Implements fetcher, runs basic unit test.
4. **Executor step 3:** Implements three parsers (one per page type).
5. **Evaluator:** Tests all three parsers against sample pages. Reports one fails.
6. **Planner (replan):** Adjusts step 3 strategy based on failure.
7. **Executor step 3 (retry):** Rewrites failing parser.
8. Continue until all steps pass.

## Notes & links

Research shows planning before execution improves task completion vs. reactive execution.
Executor can be cheaper/smaller than planner (Planner makes decisions, Executor executes them).
Add evaluation layer for code-gen to catch errors per-step before they compound.
LangGraph's cyclic graph model is natural for implementing this loop.
