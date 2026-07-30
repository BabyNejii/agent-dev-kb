---
id: action-cache-replay
title: Action caching and deterministic replay for agent debugging and cost analysis
category: operations
ecosystems: [claude-code, claude-sdk, claude-api, generic]
problem: "Agents exhibit non-deterministic behavior across runs; same prompt + context can yield different tool calls, making bugs hard to isolate and cost attribution impossible"
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [adversarial-code-review, llm-as-judge-multi-tier, self-critique-reflection-loop]
supersedes: []
sources:
  - {url: "https://github.com/nibzard/awesome-agentic-patterns#reliability--eval", kind: github, date: 2026-07-30}
  - {url: "https://github.com/ai-boost/awesome-harness-engineering#design-primitives-1", kind: github, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

Agents are inherently non-deterministic—the same prompt and context may produce different tool calls depending on temperature, reasoning process, and model state. This creates several failures:

- **Debugging:** A test fails once, then passes on retry. You cannot reproduce the failure path.
- **Cost attribution:** You cannot tell if a task cost $2 because the agent took a bad path or because the task is intrinsically expensive.
- **Regression detection:** If you change a prompt or upgrade a model, you cannot compare runs fairly—the randomness is larger than the signal.
- **Testing:** End-to-end tests become flaky; you cannot assert deterministic behavior.

## How it works

**Caching layer:** Intercept tool calls before they execute. Compute a deterministic key from the tool name, arguments, and (optionally) the agent's reasoning state. Store the result.

**Replay mechanism:** On a subsequent run with the same key, return the cached result instead of re-executing the tool. This forces the agent down the *same path* it took before.

**When to use:**
- Debugging a failed agent run (replay the exact sequence that failed)
- Cost attribution and billing (each path through the agent is reproducible and metered)
- Regression testing (compare two agent versions under identical, deterministic tool responses)
- Integration tests (mock tool responses, then replay them against real agent logic)

**When NOT to use:**
- Real-time, user-facing agents where determinism may mask actual issues (e.g., tool reliability changes)
- Tasks where tool output is time-sensitive (stock prices, rate limits)—caching stale results causes silent correctness failures
- If your cache key is too narrow (only tool name, not arguments), you'll cache incorrect matches

## Tradeoffs

| Pro | Con |
|---|---|
| Deterministic reproduction for debugging | Stale cache silently produces wrong results if tool behavior changes |
| Per-task cost becomes predictable and attributable | Cache invalidation complexity; deciding when to re-run |
| Flaky tests become deterministic | Overhead: cache hits may still be slow if agent still calls the tool speculatively |
| Can validate agent logic against mocked tools | Tool contracts must be stable for cache key to be valid |

## Setup

1. **Define a cache key function:**
   ```python
   def cache_key(tool_name: str, args: dict, agent_state: str = "") -> str:
       # Include tool name, normalized args, and optionally reasoning snapshot
       import hashlib
       key_data = f"{tool_name}:{json.dumps(args, sort_keys=True)}:{agent_state}"
       return hashlib.sha256(key_data.encode()).hexdigest()
   ```

2. **Intercept tool calls in your agent's tool runner or middleware:**
   ```python
   cache = {}  # Or persistent store (SQLite, S3)
   
   def run_tool_with_cache(tool_name: str, args: dict, agent_state: str):
       key = cache_key(tool_name, args, agent_state)
       if key in cache:
           return cache[key]  # Replay cached result
       result = execute_tool(tool_name, args)
       cache[key] = result
       return result
   ```

3. **Partition caches by scenario:**
   - Production run: fresh cache (or read-through to backend tool)
   - Regression test: locked cache (no writes, fail on cache miss)
   - Debugging: use existing cache from failed run

4. **Track cache hits/misses in observability:**
   Record which calls were cached vs. fresh for cost and correctness audits.

## Example

**Scenario:** Agent is generating code and calling a linter tool. First run:
```
Agent calls: lint(file="src/main.py")
Cache miss → runs linter → returns "3 errors"
Agent calls: lint(file="src/utils.py")
Cache miss → runs linter → returns "0 errors"
Agent modifies src/main.py and calls: lint(file="src/main.py")
Cache hit → returns "3 errors" (stale!)
```

To avoid stale results, include a version hash in the cache key:
```python
cache_key(tool_name, args, agent_state=f"file_hash:{md5(file_content)}")
```

Now the cache is implicitly invalidated if the file changes.

## Notes & links

- **Action Caching in Anthropic's harness engineering:** reported as a reliability primitive for non-deterministic agent reproduction.
- **Replay for testing:** Workflow Evals with Mocked Tools (nibzard) is a related pattern—mock the tools, cache the results, then replay against different agent versions.
- **Related entries:** [[adversarial-code-review]] (fresh-context verification), [[llm-as-judge-multi-tier]] (deterministic filters before expensive inference), [[self-critique-reflection-loop]] (iterative improvement benefits from stable cache).
- **Cache invalidation:** Phil Karlton's adage applies: cache invalidation is one of the hard problems in CS. Consider semantic versioning of tool contracts and explicit refresh signals.
