---
id: cost-budgeted-routing
title: Cost-aware model routing with hard budget caps
category: operations
ecosystems: [claude-api, claude-sdk, generic]
problem: "Unbounded agent execution wastes budget on overkill model choices; teams need runtime cost control to degrade gracefully or route to cheaper models when approaching limits"
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [supervisor-pattern, planner-executor-loop, llm-as-judge-multi-tier]
supersedes: []
sources:
  - {url: "https://github.com/nibzard/awesome-agentic-patterns#orchestration--control", kind: github, date: 2026-07-30}
  - {url: "https://github.com/ai-boost/awesome-harness-engineering#design-primitives-1", kind: github, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

Without cost awareness, agents make inefficient model choices:

- **Overspending on simple tasks:** A task that needs a 50K-token cheap model gets sent to an 200K-token frontier model because "it's more capable."
- **Budget overruns:** Long-running multi-agent pipelines exceed cost limits mid-execution with no graceful fallback.
- **No task-specific routing:** All tasks use the same model, even though some are trivial (routing, classification) and some are hard (reasoning, synthesis).
- **Opacity:** You cannot forecast cost before running the agent, so you cannot decide if a task is worth doing.

Result: A team's agent budget is exhausted by a few expensive outliers, and no one can see why.

## How it works

**Budget tracking:** Maintain a per-task, per-agent, or per-org cost budget. Track cumulative spend in real time.

**Cost estimation:** Before invoking a model, estimate the likely token count from context size and task class. Compare against remaining budget.

**Model selection:** If the estimated cost exceeds budget, route to a cheaper model or degrade to a deterministic fallback (linter, regex, static analysis).

**Hard cap enforcement:** If a task would exceed budget even with the cheapest option, fail fast instead of starting execution.

**Cost feedback loop:** Log actual cost; compare to estimate; adjust routing rules.

## Setup

1. **Define task classes and model assignments:**
   ```yaml
   tasks:
     routing:           # e.g., "which subagent should handle this?"
       model: haiku
       max_budget: $0.001
       max_tokens: 5000
     
     code-generation:   # e.g., writing a function
       model: opus
       max_budget: $0.10
       max_tokens: 50000
     
     verification:      # e.g., "is this code correct?"
       model: sonnet
       max_budget: $0.05
       max_tokens: 25000
   ```

2. **Cost estimator:**
   ```python
   def estimate_cost(task_class: str, context_tokens: int, model: str) -> float:
       # Crude: (input_tokens * input_rate) + (output_tokens * output_rate)
       # More accurate: measure historical ratio (output/input) per task class
       models = {
           "haiku":  {"input": 0.80 / 1e6, "output": 4.00 / 1e6},
           "sonnet": {"input": 3.00 / 1e6, "output": 15.00 / 1e6},
           "opus":   {"input": 15.00 / 1e6, "output": 60.00 / 1e6},
       }
       output_estimate = context_tokens * 0.3  # heuristic: output ~30% of input
       return (context_tokens * models[model]["input"] + 
               output_estimate * models[model]["output"])
   ```

3. **Route with budget awareness:**
   ```python
   def select_model_for_task(task_class: str, context_tokens: int, 
                             remaining_budget: float) -> str:
       config = task_config[task_class]
       
       # Try preferred model first
       estimated = estimate_cost(task_class, context_tokens, config["model"])
       if estimated <= remaining_budget:
           return config["model"]
       
       # Downgrade to cheaper model
       for fallback in ["haiku", "sonnet", "opus"]:
           estimated = estimate_cost(task_class, context_tokens, fallback)
           if estimated <= remaining_budget:
               return fallback
       
       # No model within budget
       raise BudgetExceededError(f"Task {task_class} estimated ${estimated:.2f}, "
                                  f"budget ${remaining_budget:.2f}")
   ```

4. **Track spend and update estimates:**
   ```python
   log_task_cost(task_id, model, input_tokens, output_tokens, actual_cost)
   # Periodically refit estimate_cost() regression on actual data
   ```

## When to use / when NOT

**Use if:**
- Organization has a fixed AI budget that must not be exceeded
- Tasks vary widely in complexity (some trivial, some hard)
- Cost is a bottleneck more than latency
- Multi-agent pipelines with unpredictable token consumption

**Do NOT use if:**
- Cost is negligible compared to business value (e.g., high-margin SaaS)
- All tasks require the same frontier model (no routing opportunity)
- Budget is so tight that graceful degradation isn't possible
- Latency SLA is tighter than the time needed for cheaper model

## Tradeoffs

| Pro | Con |
|---|---|
| Predictable total cost; never surprise overruns | Downgrading models may increase task failure rate |
| Can run more tasks within same budget | Estimation errors early in ops; requires data collection |
| Encourages task design (is this task worth $1?) | Adds latency: cost estimation before execution |
| Compound benefit: model choices become visible | Requires maintaining cost tables as model prices change |

## Example

**Scenario:** Multi-agent code review pipeline has $10 budget.

1. Agent A (planner): Decompose PR into 5 independent reviews.
   - Estimate: 8K input tokens → ~$0.02 on Sonnet → within budget ✓
   - Route to Sonnet

2. Agents B–F (reviewers): Each reads 2K lines.
   - Estimate: 12K input tokens each → $0.06 on Opus per agent → $0.30 total
   - Remaining budget: $10 - $0.02 = $9.98
   - All 5 reviewers fit within budget ✓ Route to Opus

3. Agent G (synthesizer): Summarize 5 reviews.
   - Estimate: 15K input tokens → $0.09 on Opus → $0.39 total
   - Remaining budget: $9.98 - $1.50 (actual spend from B–F) = $8.48
   - Fits ✓ Route to Opus

4. If PR was larger:
   - Revised estimate: agents B–F now 18K tokens each → $0.90/agent → $4.50 total
   - Budget remaining after A: $9.98 - $4.50 = $5.48
   - Agent G would be downgraded to Sonnet to fit within cap.

## Notes & links

- **Economic Value Signaling in Multi-Agent Networks (nibzard):** Extends this idea to agent-to-agent negotiation; agents bid for resources.
- **Non-Custodial Spending Controls (nibzard):** Fine-grained authorization (agent X can spend max $1 on search, $5 on synthesis).
- **Budget-Aware Model Routing with Hard Cost Caps (nibzard):** Foundational pattern cited here.
- **Related entries:** [[supervisor-pattern]] (task decomposition), [[planner-executor-loop]] (planning before execution), [[llm-as-judge-multi-tier]] (tiered verification using cost-aware models).
- **Real data:** LangChain reported moving a coding agent from rank 30 to top 5 on benchmarks via harness tuning (not model swap), at 1/10 the cost of frontier models.
