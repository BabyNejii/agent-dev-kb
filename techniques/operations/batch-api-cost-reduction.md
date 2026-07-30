---
id: batch-api-cost-reduction
title: Batch API for 50% cost reduction on high-volume inference
category: operations
ecosystems: [claude-api, claude-sdk]
problem: High-volume inference (evals, bulk processing, migrations) is expensive; teams pay full price even for asynchronous operations where latency doesn't matter
maturity: established
confidence: verified
effort_to_adopt: medium
works_with: [cost-budgeted-routing, token-counting-api-preflighting]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/build-with-claude/batch-processing", kind: docs, date: 2026-07-30}
  - {url: "https://platform.claude.com/docs/en/api/beta/messages/batches/create", kind: docs, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

Batch operations (test generation, large-scale evaluations, content moderation, data processing) usually don't need immediate responses. Yet submitting requests to the standard Messages API charges full price.

The Message Batches API solves this: submit 100 requests, get **50% cost reduction**, trade latency (batches typically finish within 1 hour) for savings.

For teams running 1000s of requests weekly, the difference is substantial: $1000 → $500.

## How it works

Instead of sending messages one at a time:

1. Package your requests into a JSON array with unique request IDs
2. Send them to `/v1/messages/batches`
3. Anthropic processes all of them asynchronously (usually within 1 hour, up to 24 hours)
4. Poll for status or retrieve results when ready

Each request in the batch is handled independently; failures don't block others. You pay the discounted rate regardless of how long the batch takes.

## Setup

**Python SDK (Anthropic SDK does not yet expose Batches directly; use REST or a wrapper):**

Using raw HTTP:
```python
import json
import requests
import time

api_key = "your-api-key"

# Prepare batch requests
requests_batch = [
    {
        "custom_id": f"eval_{i}",
        "params": {
            "model": "claude-opus-4-6",
            "messages": [
                {"role": "user", "content": f"Evaluate test case #{i}"}
            ],
            "max_tokens": 512,
        },
    }
    for i in range(100)
]

# Submit batch
response = requests.post(
    "https://api.anthropic.com/v1/messages/batches",
    json={"requests": requests_batch},
    headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "message-batches-2024-09-24",
    },
)

batch = response.json()
batch_id = batch["id"]
print(f"Batch {batch_id} submitted. Status: {batch['status']}")

# Poll for completion
while True:
    status = requests.get(
        f"https://api.anthropic.com/v1/messages/batches/{batch_id}",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "message-batches-2024-09-24",
        },
    ).json()
    
    if status["status"] in ["completed", "failed", "expired"]:
        print(f"Batch {status['status']}")
        break
    
    print(f"Status: {status['status']}, processed: {status.get('processing_count', 0)}")
    time.sleep(30)

# Retrieve results
results = requests.get(
    f"https://api.anthropic.com/v1/messages/batches/{batch_id}/results",
    headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "message-batches-2024-09-24",
    },
).json()

for result in results["results"]:
    print(f"{result['custom_id']}: {result['response']['content'][0]['text']}")
```

## When to use / when NOT

**Use Batch API when:**
- Running 100+ requests in a single job
- Latency tolerance is ≥ 1 hour (evals, migrations, content moderation, bulk analysis)
- Saving 50% of cost is more valuable than immediate results
- Building overnight batch jobs (test generation, report generation)

**DO NOT use when:**
- You need results in seconds (chat, real-time API, streaming)
- You have just 1–10 requests (not worth the polling complexity)
- Your workflow requires immediate feedback loops (interactive debugging, live chat)

## Tradeoffs

**Pros:**
- 50% cost reduction on all requests in the batch
- Straightforward to implement: just POST a JSON array
- No throughput limits; submit 100K requests in one batch
- Each request fails or succeeds independently

**Cons:**
- Asynchronous: can't get results immediately; typical latency is 1 hour but up to 24 hours possible
- Polling overhead: you need to check status yourself (SDK support is limited)
- Request size: each request in the batch must be ≤ ~200KB (total batch ≤ 1GB)
- No streaming: each response is a complete message, not streamed tokens

## Example

**Overnight test generation with 50% savings:**
```python
# Generate tests for 1000 functions overnight
functions = load_functions_from_codebase()

batch_requests = [
    {
        "custom_id": f"test_{func.id}",
        "params": {
            "model": "claude-opus-4-6",
            "messages": [
                {
                    "role": "user",
                    "content": f"Write unit tests for:\n\n{func.code}",
                }
            ],
            "max_tokens": 1024,
        },
    }
    for func in functions
]

# Submit, go home, check results tomorrow
batch_id = submit_batch(batch_requests)
print(f"Batch {batch_id} submitted. Check back in ~1 hour.")

# Next morning: retrieve all results
results = poll_and_fetch_results(batch_id)
for result in results:
    save_generated_test(result["custom_id"], result["response"]["content"][0]["text"])
```

**Bulk evaluation with cost tracking:**
```python
test_cases = load_test_cases(10000)
batch_size = 1000

for i in range(0, len(test_cases), batch_size):
    batch = test_cases[i : i + batch_size]
    batch_requests = [
        {
            "custom_id": f"test_{case.id}",
            "params": {
                "model": "claude-opus-4-6",
                "messages": [{"role": "user", "content": case.prompt}],
                "max_tokens": 256,
            },
        }
        for case in batch
    ]
    
    batch_id = submit_batch(batch_requests)
    # With Batch API: cost = input_tokens * 0.5 * price_per_mtok
    # vs standard API cost = input_tokens * price_per_mtok
    # Savings = 50%
```

## Notes & links

- Batch processing is Anthropic's recommended approach for all non-interactive, high-volume inference
- Typical batch completion: < 1 hour. Max: 24 hours. Most finish within the SLA
- The 50% discount applies to input and output tokens; cache reads are also discounted
- Combine with [[token-counting-api-preflighting]] to estimate batch cost before submission
- Works alongside [[cost-budgeted-routing]] for even smarter cost control (route simple queries to Sonnet, complex to Opus, batch to Haiku)
- Official documentation: https://platform.claude.com/docs/en/build-with-claude/batch-processing
- API reference: https://platform.claude.com/docs/en/api/messages/batches
