---
id: supervisor-pattern
title: Supervisor pattern for hierarchical task decomposition
category: orchestration
ecosystems: [claude-code, claude-sdk, generic]
problem: Complex tasks overwhelm a single agent's context; need centralized task decomposition with specialized workers.
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [planner-executor-loop, subagent-fan-out]
supersedes: []
sources:
  - {url: "https://fast.io/resources/ai-agent-supervisor-pattern/", kind: blog, date: 2026-07-28}
  - {url: "https://medium.com/aitech/the-supervisor-pattern-for-gen-ai-agent-systems-d1920c0bdbbb", kind: blog, date: 2026-07-28}
  - {url: "https://agentic-design.ai/patterns/multi-agent/supervisor-worker-pattern", kind: docs, date: 2026-07-28}
  - {url: "https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system", kind: docs, date: 2026-07-28}
added: 2026-07-28
updated: 2026-07-28
---

## Problem

A single agent cannot hold complex workflows in context while performing specialist work (code generation, testing, review). Decomposition must happen upfront, and workers must specialize per task—but coordinating this statically leads to rigid, un-adaptive workflows.

## How it works

One **supervisor agent** receives the high-level goal, decomposes it into logical subtasks, and routes each to a specialized **worker agent**. The supervisor:
1. Breaks the task into non-overlapping subtasks.
2. Routes each to an appropriate worker (e.g., "CodeGen" for implementation, "Reviewer" for testing).
3. Monitors task dependencies and execution order.
4. Aggregates results and handles failures.

Workers operate independently in their own contexts and only report results back to the supervisor—they do not see each other's outputs during execution.

## Setup

In Claude Code, define worker agents in `.claude/agents/`:
```
.claude/agents/
  - code-generator.md
  - code-reviewer.md
  - test-writer.md
```

Supervisor orchestrates:
```python
# Supervisor reads task, decomposes
subtasks = supervisor.decompose(user_request)
# [("Design schema", "designer"), ("Implement API", "code-gen"), ("Write tests", "tester")]

# Route in parallel (Claude Code) or sequentially (SDK)
results = {}
for subtask_desc, worker_name in subtasks:
    results[worker_name] = Agent(
        description=f"Worker: {worker_name}",
        prompt=f"Task: {subtask_desc}"
    ).run()

# Aggregate and validate
supervisor.validate_and_merge(results)
```

## When to use / when NOT

- **USE** for tasks that decompose naturally (e.g., feature: design → code → test → docs).
- **USE** when workers are stateless and work can happen in parallel without blocking.
- **USE** for code generation, testing, review pipelines.
- **NOT** for highly interdependent tasks where one worker's output is another's input (use [[planner-executor-loop]] instead).
- **NOT** for one-off lookups or simple queries.

## Tradeoffs

- **Cost:** Multiple agents, each with full context of their task. Cost scales with number of workers and context size.
- **Coordination overhead:** Task decomposition, routing, and result aggregation add latency. Not faster for simple single-agent tasks.
- **Quality:** By isolating workers, you prevent "hallucination loops" where one agent tries to do too many things. Workers focus, reducing errors.
- **Scalability:** Easy to add new worker roles without retraining supervisor. New workers integrate by extending the decomposition logic.

## Example

Building a REST API from a spec:
1. **Supervisor** reads spec, creates tasks: "Design schema", "Generate code", "Write integration tests", "Update swagger docs".
2. **Schema Designer** outputs database schema and relationships.
3. **Code Generator** reads schema, writes handler code.
4. **Test Writer** reads code, writes integration tests.
5. **Doc Writer** reads code and tests, updates swagger.
6. **Supervisor** merges results, runs CI, and validates schema + code + tests + docs are consistent.

All workers operate in parallel with supervisor coordination.

## Notes & links

This is the most widely supported pattern across frameworks (LangGraph, Claude SDK, LangChain).
Hierarchical variant: supervisor decomposes, then each worker spawns sub-workers (two levels deep).
Dynamic variant: supervisor determines number of workers at runtime based on task complexity.
See [[subagent-fan-out]] for the read-only variant where sub-agents search independent angles.
