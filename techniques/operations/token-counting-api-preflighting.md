---
id: token-counting-api-preflighting
title: Token counting API for pre-request cost estimation
category: operations
ecosystems: [claude-api, claude-sdk, claude-code]
problem: You can't estimate token usage before sending a request, so you can't budget or prevent overspending on expensive operations
maturity: established
confidence: verified
effort_to_adopt: low
works_with: [cost-budgeted-routing, batch-api-cost-reduction]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/api/beta/messages/count_tokens", kind: docs, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

In multi-agent systems and high-volume inference, you need to know token consumption *before* making API calls to:
- Enforce budget limits (avoid surprise overages)
- Route tasks to cheaper models dynamically
- Batch or defer expensive operations
- Validate that prompts fit within context windows

Without upfront estimation, teams discover cost problems *after* the invoice arrives.

## How it works

The `/v1/messages/count_tokens` endpoint takes your exact message content, system prompt, and tools — and returns the token count that would be consumed **without** sending the actual request.

The response includes:
- `input_tokens` — total tokens for messages + system + tools
- `context_management` — info about context optimization applied

This is the same tokenizer the actual API uses, so counts are accurate.

## Setup

**Python SDK:**
```python
from anthropic import Anthropic

client = Anthropic()

# Count tokens before committing to a request
response = client.messages.count_tokens(
    model="claude-opus-4-6",
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Summarize a 100-page paper..."}
    ],
)

input_tokens = response.input_tokens
print(f"This request will cost {input_tokens} input tokens")

# Only proceed if within budget
if input_tokens < MAX_TOKENS_PER_REQUEST:
    actual = client.messages.create(
        model="claude-opus-4-6",
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": "Summarize a 100-page paper..."}],
        max_tokens=1024,
    )
```

**REST API:**
```bash
curl https://api.anthropic.com/v1/messages/count_tokens \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-4-6",
    "system": "You are a helpful assistant.",
    "messages": [
      {"role": "user", "content": "Summarize a 100-page paper..."}
    ]
  }'
```

Returns:
```json
{
  "input_tokens": 2143,
  "context_management": {
    "original_input_tokens": 2143
  }
}
```

## When to use / when NOT

**Use when:**
- Building gated systems where expensive tasks need approval before executing
- Running large-scale evaluations and want per-task cost visibility before commitment
- Multi-agent workflows where a supervisor needs to decide whether a subtask is worth the token cost
- Long context operations (RAG, document analysis) where actual token count varies wildly

**NOT needed for:**
- Real-time conversational systems where latency matters more than upfront cost prediction
- Systems with fixed, pre-validated prompts where counts are known
- Streaming responses where you're already committed to the request

## Tradeoffs

**Pros:**
- Exact cost predictability before incurring charges
- No double-API-call overhead if counts are already reasonable
- Works with system prompts, tools, and complex message arrays

**Cons:**
- One extra API call per estimation (minimal cost, typically 10-100 tokens, negligible)
- Doesn't predict *output* token count — only input (output depends on model behavior)
- Context management (e.g., compaction) may change counts at request time if content exceeds limits

## Example

**Multi-agent orchestrator with cost gating:**
```python
from anthropic import Anthropic

client = Anthropic()
MAX_AGENT_TASK_BUDGET = 50000  # tokens

def should_delegate_to_agent(task_prompt, agent_system_prompt):
    """Decide whether to let an agent handle this task without exceeding budget."""
    response = client.messages.count_tokens(
        model="claude-opus-4-6",
        system=agent_system_prompt,
        messages=[{"role": "user", "content": task_prompt}],
    )
    
    if response.input_tokens > MAX_AGENT_TASK_BUDGET:
        print(f"Task too expensive: {response.input_tokens} tokens > budget {MAX_AGENT_TASK_BUDGET}")
        return False
    
    print(f"Delegating task ({response.input_tokens} tokens)")
    return True
```

**Cost-aware routing in evaluation loop:**
```python
# For each test case in a large evaluation set, estimate cost
# Then batch high-cost cases separately with cheaper model, cheap cases with expensive model
for test_case in test_cases:
    token_estimate = client.messages.count_tokens(
        model="claude-opus-4-6",
        messages=[{"role": "user", "content": test_case}],
    )
    
    if token_estimate.input_tokens < 5000:
        queue_for_model("claude-sonnet", test_case)  # fast, cheaper
    else:
        queue_for_model("claude-opus-4-6", test_case)  # powerful for large contexts
```

## Notes & links

- Token counting is instantaneous and uses the same tokenization logic as actual API calls
- Cache-aware counting: if your prompts use prompt caching, counts reflect cached content separately
- The count includes all overhead (system prompts, tool definitions, message formatting)
- Useful companion to [[cost-budgeted-routing]] and [[batch-api-cost-reduction]] for comprehensive cost control
- Official API reference: https://platform.claude.com/docs/en/api/beta/messages/count_tokens
