---
id: multi-agent-cost-attribution-sdk
title: Per-session cost tracking for multi-agent deployments
category: operations
ecosystems: [claude-sdk, claude-api]
problem: When you run multiple subagents or parallel tasks, total cost is visible but per-agent or per-task attribution is opaque, blocking cost optimization and billing allocation
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [agent-sdk-otel-observability, cost-budgeted-routing]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/agent-sdk/cost-tracking", kind: docs, date: 2026-07-30}
  - {url: "https://github.com/nibzard/awesome-agentic-patterns#orchestration--control", kind: github, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

In production multi-agent systems, you may run:
- A supervisor agent that spawns multiple specialist subagents
- A batch of parallel data-processing agents
- A cascade of agents (planner → executor → reviewer)

When costs spike or you need to bill different teams/customers for agent work, the question becomes: **which agent spent what?** Without per-agent attribution, you're left with:
- Total bill from API (opaque)
- Aggregated token counts across all agents
- No way to optimize individual agents or allocate costs to cost centers

This is especially painful when:
- A buggy subagent loops and wastes tokens
- You want to upgrade one agent's model while keeping others on cheaper models
- You're billing customers per-task and need granular cost attribution
- You're A/B testing agent implementations and need side-by-side cost comparison

## How it works

The Agent SDK assigns a `session_id` to each `query()` call. When you instantiate multiple agent instances with the same session or different sessions, you can:

1. **Isolate session IDs per agent** — each `ClaudeAgentOptions` gets its own session identifier
2. **Read cost from the response stream** — every response chunk carries token usage and cost estimates
3. **Aggregate per-session** — sum cost across all chunks for one agent and correlate it to the agent's identity

The Agent SDK exposes token usage synchronously in the response, so you don't need an external backend:

```python
# Pseudocode: cost appears in every message from query()
async for message in query(...):
    if message.type == "final_response":
        token_usage = message.usage  # { input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens }
        estimated_cost = message.cost  # float (calculated locally from token counts and model rates)
```

By tagging each session with metadata (agent name, customer ID, task type, etc.), you can:
- Write cost records to a database or metrics backend
- Group by agent/customer/task in analytics
- Detect cost anomalies per agent
- Bill or chargeback per unit

## Setup

### Basic per-agent session tracking (Python)

```python
import asyncio
import uuid
from claude_agent_sdk import query, ClaudeAgentOptions
from dataclasses import dataclass

@dataclass
class AgentCostTracker:
    agent_name: str
    customer_id: str
    task_id: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost: float = 0.0

async def run_agent_with_cost_tracking(
    agent_name: str, 
    customer_id: str, 
    prompt: str
) -> AgentCostTracker:
    """Run an agent and track its costs independently."""
    
    task_id = str(uuid.uuid4())
    tracker = AgentCostTracker(
        agent_name=agent_name,
        customer_id=customer_id,
        task_id=task_id
    )
    
    # Assign a unique session ID per agent/task combination
    session_id = f"{agent_name}-{customer_id}-{task_id}"
    
    options = ClaudeAgentOptions(
        session_id=session_id,
        # Optional: export to OpenTelemetry with per-agent attributes
        env={
            "OTEL_RESOURCE_ATTRIBUTES": f"agent.name={agent_name},customer.id={customer_id}",
        }
    )
    
    async for message in query(prompt=prompt, options=options):
        if message.type == "final_response":
            # Cost data is available synchronously
            if hasattr(message, "usage"):
                tracker.total_input_tokens = message.usage.input_tokens
                tracker.total_output_tokens = message.usage.output_tokens
            if hasattr(message, "cost"):
                tracker.estimated_cost = message.cost
    
    return tracker

async def main():
    # Simulate a supervisor spawning multiple specialist agents
    results = []
    tasks = [
        run_agent_with_cost_tracking("research-agent", "customer-123", "Research best practices"),
        run_agent_with_cost_tracking("writing-agent", "customer-123", "Write a summary"),
        run_agent_with_cost_tracking("review-agent", "customer-123", "Review for quality"),
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Aggregate and report per agent
    print("Cost Attribution Report:")
    total_cost = 0
    for tracker in results:
        print(f"{tracker.agent_name:20} | ${tracker.estimated_cost:8.4f} | {tracker.total_input_tokens} in, {tracker.total_output_tokens} out")
        total_cost += tracker.estimated_cost
    
    print(f"{'TOTAL':20} | ${total_cost:8.4f}")
```

### Storing costs for billing/analytics (Django + PostgreSQL example)

```python
# models.py
from django.db import models

class AgentCostRecord(models.Model):
    agent_name = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=100)
    task_id = models.CharField(max_length=100, unique=True)
    session_id = models.CharField(max_length=200)
    
    input_tokens = models.IntegerField()
    output_tokens = models.IntegerField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["customer_id", "created_at"]),
            models.Index(fields=["agent_name", "created_at"]),
        ]

# In your agent runner
async def run_agent_with_billing(agent_name, customer_id, prompt):
    tracker = await run_agent_with_cost_tracking(agent_name, customer_id, prompt)
    
    # Persist for later analysis
    AgentCostRecord.objects.create(
        agent_name=tracker.agent_name,
        customer_id=tracker.customer_id,
        task_id=tracker.task_id,
        session_id=f"{agent_name}-{customer_id}-{tracker.task_id}",
        input_tokens=tracker.total_input_tokens,
        output_tokens=tracker.total_output_tokens,
        estimated_cost=float(tracker.estimated_cost),
    )
```

### Supervisor spawning subagents with per-subagent cost tracking

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def supervisor_agent_with_cost_breakdown(task_description: str):
    """Supervisor orchestrates subagents and reports per-subagent costs."""
    
    subagent_costs = {}
    
    # Create subagents, each with its own session
    specialist_prompts = {
        "data-extractor": f"Extract structured data from: {task_description}",
        "validator": f"Validate the extracted data: {task_description}",
        "formatter": f"Format into final output: {task_description}",
    }
    
    tasks = []
    for agent_id, prompt in specialist_prompts.items():
        options = ClaudeAgentOptions(
            session_id=f"supervisor-{agent_id}-{uuid.uuid4()}",
        )
        
        async def run_and_track(aid, p):
            cost = 0
            async for msg in query(p, options=ClaudeAgentOptions(session_id=f"supervisor-{aid}-{uuid.uuid4()}")):
                if hasattr(msg, "cost"):
                    cost = msg.cost
            subagent_costs[aid] = cost
        
        tasks.append(run_and_track(agent_id, prompt))
    
    await asyncio.gather(*tasks)
    
    # Report breakdown
    print("Subagent Cost Breakdown:")
    for agent_id, cost in subagent_costs.items():
        print(f"  {agent_id:20} ${cost:.4f}")
    
    return subagent_costs
```

## When to use / when NOT

**Use this when:**
- You run multiple agents in a single deployment and need cost visibility per agent
- You want to bill customers per task and need granular cost attribution
- You're optimizing which agents run in production and need baseline costs
- You're A/B testing agent configurations and need cost comparison
- You want to detect runaway agents (infinite loops, repeated retries) and trigger cost limits

**Do not use when:**
- You are satisfied with aggregate cost tracking (total spend is all you need)
- Your deployment runs a single agent (use `/cost` slash command in Claude Code CLI instead)
- Your backend/database cannot handle per-call cost inserts (high-volume scenarios — consider batching)

## Tradeoffs

**Advantages:**
- Cost attribution is synchronous and does not require external observability infrastructure
- Session IDs are built into the SDK; no custom wrapping needed
- Works offline — no dependency on a centralized backend
- Granular per-task/per-agent cost accounting
- Can correlate costs to business metrics (customer, feature, task type)

**Disadvantages:**
- Requires instrumentation in application code to track sessions and write to your cost store
- Token counts are estimates of what the API will bill; actual bill may differ slightly
- Does not capture costs if the agent crashes before returning a response
- Requires a cost-tracking table/system (additional database cost)
- In very high-volume scenarios, writing one cost record per query can overwhelm your database (batch inserts help)

## Example

**Multi-tenant SaaS: billing per customer per month**

```python
# Periodic aggregation job (daily/weekly)
from django.db.models import Sum
from decimal import Decimal

def generate_customer_cost_report():
    from dateutil import relativedelta
    last_month = datetime.now() - relativedelta.relativedelta(months=1)
    
    report = AgentCostRecord.objects \
        .filter(created_at__gte=last_month) \
        .values("customer_id", "agent_name") \
        .annotate(total_cost=Sum("estimated_cost")) \
        .order_by("customer_id")
    
    for row in report:
        print(f"Customer {row['customer_id']}: {row['agent_name']} ${row['total_cost']:.2f}")
    
    # Trigger billing events
    customer_totals = {}
    for row in report:
        cid = row["customer_id"]
        if cid not in customer_totals:
            customer_totals[cid] = Decimal(0)
        customer_totals[cid] += row["total_cost"]
    
    for customer_id, total_cost in customer_totals.items():
        emit_billing_event(customer_id, total_cost)
```

## Notes & links

- [[agent-sdk-otel-observability]] — for detailed traces and metrics in addition to cost tracking
- [[cost-budgeted-routing]] — for enforcing hard cost limits per agent or task
- **Timing caveat:** Cost estimates are calculated locally from token counts and published model rates. The actual API bill may differ slightly due to rounding or rate changes. The **Usage** page in the Claude Console is authoritative for billing.
- **Session context:** `session_id` is optional. If not provided, the SDK generates one. Explicitly set session IDs to ensure you can correlate cost records to your business domain.
- **Batch inserts:** In high-volume production (1000+ agent calls/day), batch cost inserts into your database rather than inserting per-call to avoid database saturation.
