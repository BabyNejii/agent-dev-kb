---
id: subagent-test-generation-bulk
title: Subagent Orchestration for Bulk Test Generation
category: codebase-ops
ecosystems: [claude-code, claude-sdk]
problem: Single agent degrades in quality over many iterations on large codebases; test generation stalls
maturity: emerging
confidence: verified
effort_to_adopt: medium
works_with: []
supersedes: []
sources:
  - {url: "https://code.claude.com/docs/en/agent-sdk/subagents", kind: docs, date: "2026-07-28"}
  - {url: "https://www.codecentric.de/en/knowledge-hub/blog/16000-tests-in-4-days-reaching-80-percent-test-coverage-with-claude-code", kind: blog, date: "2026-07-28"}
  - {url: "https://medium.com/airwallex-engineering/how-we-used-claude-code-subagents-to-cut-integration-testing-from-2-weeks-to-2-hours-8a19ed7793f8", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Asking a single agent to generate tests for a large codebase causes context degradation: as the agent accumulates knowledge of files, coverage gaps, and test patterns, its output quality declines. Generating 16,000 tests manually would take months; asking one agent to do it all loses coherence and introduces redundancy.

## How it works

The **controller + disposable subagents** pattern solves this by partitioning work. A main orchestrator agent measures coverage, selects targets, and spawns isolated single-purpose subagents — each knows only one unit (class, module, function) and terminates after completion. Fresh context per subagent means consistent quality; the controller coordinates without accumulating context noise.

**Architecture:**
1. **Controller Agent:** Coverage analyzer, test target selector, subagent spawner, result aggregator
2. **Subagent Specialists:** Fresh agent per unit (test generation, review, debugging, gap analysis)
3. **Verification Layer:** Post-generation review and test validation

## Setup

**In the Agent SDK (Python example):**
```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def main():
    async for message in query(
        prompt="""Analyze test coverage, then:
1. Identify the next untested class (read coverage report)
2. Spawn a Test Generator subagent to write tests for that class only
3. Collect results and repeat until 80% coverage
4. Report final coverage and test counts""",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Bash", "Glob", "Grep", "Agent"],
            agents={
                "test-generator": AgentDefinition(
                    description="Generate unit tests for a single class",
                    prompt="Write comprehensive unit tests for the given class. Include happy path, error cases, and edge cases. Aim for ~80% line coverage.",
                    tools=["Read", "Write", "Bash", "Grep"]
                ),
                "test-reviewer": AgentDefinition(
                    description="Review generated tests for quality and coverage",
                    prompt="Review the test suite. Check for: redundancy, coverage gaps, edge cases, naming clarity. Report issues.",
                    tools=["Read", "Grep"]
                )
            }
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

**Workflow loop in the controller:**
```python
# Pseudocode for controller logic
while coverage < TARGET_COVERAGE:
    coverage_report = run_coverage()
    untested_class = select_next_target(coverage_report)
    
    # Spawn fresh subagent — isolated context, one job
    await spawn_subagent("test-generator", 
        prompt=f"Write tests for {untested_class}")
    
    # Collect & aggregate
    test_results = collect_from_subagent()
    coverage = re_measure_coverage()
```

## When to use / when NOT

**Use when:**
- Codebase exceeds 10k LOC and needs test coverage
- Multiple classes/modules need tests (>5 units)
- Test quality consistency matters (e.g., must pass review gates)
- Team size is small and can't split testing manually

**Don't use when:**
- Codebase is small (<2k LOC); single agent is simpler
- Tests need deep business logic understanding (heavily context-dependent)
- Real-time iteration is required (subagent spawning adds latency)

## Tradeoffs

**Pros:**
- Consistent output quality (fresh agent per unit = clean context)
- Scales to thousands of tests without degradation
- Parallelizable (spawn multiple subagents concurrently)
- Easy to specialize subagents (generation, review, debugging, analysis)
- Proven to raise coverage from 58% to 82% in 4 days on real codebases

**Cons:**
- Overhead of spawning agents (latency per batch)
- Requires orchestration logic (controller must be reliable)
- Higher token consumption than a single agent (each subagent pays its own context tax)
- Subagents can't learn from each other (no cross-unit knowledge sharing)

## Example

**Real case (codecentric):**
- Starting state: 58% line coverage, large Java codebase
- Team: 3 engineers, 4 working days
- Process: Controller identifies untested classes → spawns Test Generator → collects results → re-measures
- Result: 16,000 new tests, 82% coverage in 4 days

**Another pattern (Airwallex):**
- Spawn 5 specialist subagents in parallel:
  - Happy path generator
  - Error/unhappy path generator
  - State transition tester
  - Dependency injection tester
  - End-to-end flow tester
- Each generates a slice of the test suite
- Test Reviewer agent dedupes and validates
- Reduced integration test time from 2 weeks to 2 hours

## Notes & links

- **Batch strategy:** Generate 5–10 tests per cycle, review, feedback, repeat — helps calibrate agent expectations
- **Coverage target:** Aim for ~80% coverage, not 100%; diminishing returns beyond 80%, and AI tests serve double duty (validation + documentation)
- **Large context window advantage:** Feed entire codebase requirements/schemas in first controller prompt; enables generation of cross-unit integration tests
- **Specialized agents:** Pair generation agents with dedicated Review and Debugging agents to catch quality issues early
