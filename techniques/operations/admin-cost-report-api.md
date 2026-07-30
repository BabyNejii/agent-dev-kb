---
id: admin-cost-report-api
title: Admin Cost Report API for organization-wide spend tracking
category: operations
ecosystems: [claude-api]
problem: Multi-team or multi-project organizations can't see which models, agents, or projects consumed how much, making cost attribution and budgeting invisible
maturity: established
confidence: verified
effort_to_adopt: low
works_with: [cost-budgeted-routing, token-counting-api-preflighting]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/api/admin/cost_report/retrieve", kind: docs, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

When a team runs multiple agents or projects, the bill arrives showing total spend—but not which work caused it. You can't:
- Attribute costs to specific agents or projects
- Detect cost regressions (e.g., a change that tripled token usage)
- Budget per team or per model
- Audit whether expensive models are being overused

Without cost attribution, teams can't optimize.

## How it works

The Admin Cost Report API (`GET /v1/organizations/cost_report`) returns cost data broken down by:
- **Model** — which Claude version was used
- **Token type** — uncached input, cache creation, cache read, output
- **Context window** — 0-200K, 200K-1M (affects pricing)
- **Service tier** — standard or batch
- **Time bucket** — daily cost breakdowns
- **Inference geo** — which region inference ran

This lets you see exactly which model variant and workload type consumed how much.

## Setup

**Requirements:**
- Organization-level API key (not a user key)
- `anthropic-version: 2023-06-01` header

**Python:**
```python
import requests

org_api_key = "your-org-api-key"

response = requests.get(
    "https://api.anthropic.com/v1/organizations/cost_report",
    headers={
        "Authorization": f"Bearer {org_api_key}",
        "anthropic-version": "2023-06-01",
    },
)

cost_report = response.json()

# Example response structure:
# {
#   "data": [
#     {
#       "starting_at": "2026-07-29T00:00:00Z",
#       "ending_at": "2026-07-30T00:00:00Z",
#       "results": [
#         {
#           "model": "claude-opus-4-6",
#           "token_type": "uncached_input_tokens",
#           "context_window": "0-200k",
#           "service_tier": "standard",
#           "amount": "123.45",
#           "currency": "USD"
#         },
#         ...
#       ]
#     }
#   ],
#   "has_more": false
# }

for day in cost_report["data"]:
    print(f"\n{day['starting_at']}")
    for cost_line in day["results"]:
        print(f"  {cost_line['model']} {cost_line['token_type']}: ${cost_line['amount']}")
```

**curl:**
```bash
curl "https://api.anthropic.com/v1/organizations/cost_report" \
  -H "Authorization: Bearer $ORG_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

**Optional query parameters:**
- `start_date` — ISO date (e.g., `2026-07-01`)
- `end_date` — ISO date
- `page` — for pagination if report is large

## When to use / when NOT

**Use when:**
- You need to understand organization-wide spend by model (e.g., "Opus costs 10x more than Sonnet")
- You want to detect cost anomalies (e.g., a spike from a deployment)
- You're budgeting per team or project and need to map costs back
- You're deciding whether to upgrade to a higher usage tier
- You need to report spend to finance or stakeholders

**NOT needed for:**
- Individual session/message cost tracking (use message-level `usage` fields instead)
- Real-time per-request cost (too coarse-grained; reports are daily)
- Local development where one key is used by one developer

## Tradeoffs

**Pros:**
- Aggregated across your entire organization, no per-request logging needed
- Breaks down by model, token type, and context window — actionable granularity
- Time-bucketed data lets you spot trends
- Built-in, no additional tracking infrastructure needed

**Cons:**
- Daily granularity only (not per-request or per-hour)
- Doesn't directly map costs to specific agents or projects (you must correlate via logs)
- Organization-level API key required (can't delegate to team leads easily)
- Historical data may have a 24–48-hour lag

## Example

**Detecting a cost regression after a deploy:**
```python
def check_cost_anomaly(days_to_check=3, threshold_multiplier=1.5):
    """Alert if today's cost is 1.5x yesterday's."""
    org_key = get_org_api_key()
    
    report = requests.get(
        "https://api.anthropic.com/v1/organizations/cost_report",
        headers={
            "Authorization": f"Bearer {org_key}",
            "anthropic-version": "2023-06-01",
        },
    ).json()
    
    daily_totals = {}
    for day_bucket in report["data"]:
        day = day_bucket["starting_at"].split("T")[0]
        total = sum(float(r["amount"]) for r in day_bucket["results"])
        daily_totals[day] = total
    
    dates = sorted(daily_totals.keys())
    if len(dates) >= 2:
        yesterday = daily_totals[dates[-2]]
        today = daily_totals[dates[-1]]
        
        if today > yesterday * threshold_multiplier:
            print(f"⚠️  Cost spike: ${yesterday:.2f} → ${today:.2f}")
            return True
    return False
```

**Choosing model tier based on actual usage:**
```python
def model_cost_distribution():
    """See which models are driving costs."""
    org_key = get_org_api_key()
    
    report = requests.get(
        "https://api.anthropic.com/v1/organizations/cost_report",
        headers={
            "Authorization": f"Bearer {org_key}",
            "anthropic-version": "2023-06-01",
        },
    ).json()
    
    model_costs = {}
    for day_bucket in report["data"]:
        for result in day_bucket["results"]:
            model = result["model"]
            if model not in model_costs:
                model_costs[model] = 0
            model_costs[model] += float(result["amount"])
    
    for model, cost in sorted(model_costs.items(), key=lambda x: -x[1]):
        print(f"{model}: ${cost:.2f}")
    
    # If 80% of cost is on Opus, maybe consider using Sonnet for simpler tasks
```

**Correlating costs with deployments:**
```python
# Example: match cost spike to deploy timestamp
deploy_log = {
    "2026-07-28T15:30:00Z": "v2.1 - added new RAG pipeline",
    "2026-07-29T09:00:00Z": "v2.2 - fixed token counting bug",
}

cost_report = fetch_org_cost_report()

for day_bucket in cost_report["data"]:
    date = day_bucket["starting_at"].split("T")[0]
    total = sum(float(r["amount"]) for r in day_bucket["results"])
    
    # Check if any deploys happened that day
    deploys_that_day = [v for k, v in deploy_log.items() if k.startswith(date)]
    if deploys_that_day:
        print(f"{date}: ${total:.2f} (deploys: {deploys_that_day})")
```

## Notes & links

- Cost Report API is the source of truth for billing; all costs here match your invoice
- Token types in the report:
  - `uncached_input_tokens` — standard input tokens
  - `cache_creation_input_tokens` — tokens used to create prompt cache entries
  - `cache_read_input_tokens` — cached tokens that were re-read (cheaper than uncached)
  - `output_tokens` — model-generated tokens
- For attribution across agents, combine with application-level logging (e.g., tag each agent's API calls with an ID, then correlate with cost reports)
- Works alongside [[cost-budgeted-routing]] to enforce per-team or per-project budgets
- Useful companion to [[token-counting-api-preflighting]] for end-to-end cost visibility
- Official documentation: https://platform.claude.com/docs/en/api/admin/cost_report/retrieve
