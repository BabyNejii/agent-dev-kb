---
id: prompt-caching-with-claude-api
title: Prompt caching to reduce API costs and latency
category: context
ecosystems: [claude-api]
problem: Long, repetitive prompts (system instructions, large contexts) re-sent on every request waste tokens and latency
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [instruction-hierarchy-layering]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/build-with-claude/prompt-caching", kind: docs, date: "2026-07-28"}
  - {url: "https://www.anthropic.com/news/prompt-caching", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Production agents send large stable prefixes on every request: system instructions, tool definitions, retrieved documents, or conversation history. Without caching, each request pays the full token cost and latency penalty for re-processing identical content.

## How it works

Claude API caches frequently used prompt prefixes and charges ~10% of input cost to read from cache on subsequent requests. The first request with a prefix pays ~1.25-2x cost to write the cache (depending on TTL). Cached content still counts toward context window limits, but the cost and latency savings are dramatic.

The system matches incoming requests against cached prefixes. When it finds a match within the TTL window (default 5 min, optional 1 hour), the model reuses the cached computation.

## Setup

**Automatic caching (simplest):**
```python
response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    cache_control={"type": "ephemeral"},  # Add this
    system="You are a helpful assistant...",
    messages=[...]
)
```

**Explicit breakpoints (fine-grained):**
Mark the last block whose prefix is identical across requests. Place `cache_control` on individual content blocks:
```python
{
    "type": "text",
    "text": "[large stable context here]",
    "cache_control": {"type": "ephemeral"}  # Move to last shared block only
}
```

**TTL Options:**
- Default: 5-minute TTL, free refreshes within window
- 1-hour: `{"type": "ephemeral", "ttl": "1h"}` for less frequent requests

**Minimum cacheable length** (model-dependent):
- Opus 5, Fable 5: 512 tokens
- Sonnet 5, Opus 4.8: 1,024 tokens
- Haiku 4.5, Opus 4.5: 4,096 tokens

## When to use / when NOT

**Use when:**
- System prompt exceeds 1,000 tokens and you make >few requests/hour
- Sending retrieved context (5,000-30,000 tokens) per request in RAG applications
- Scaling multi-turn conversations or agent sessions
- Cost savings matter (60-90% reduction is common)

**NOT when:**
- Prompt content changes on every request (timestamps, per-user data, etc.) — every change invalidates the cache
- Minimum cacheable length not met — prompt too short for the model
- One-shot requests — no benefit from caching a single prompt

## Tradeoffs

**Benefits:**
- 60-90% input cost reduction on cached requests
- Reduced latency for re-processing stable content
- Cache reads pay only 0.1x base input cost

**Costs & limitations:**
- First request pays ~1.25-2x to write cache
- Cached content still occupies context window
- Cache must be byte-identical to hit — timestamps, whitespace inconsistencies, or user-specific data break hits
- TTL window limits reuse (5 min or 1 hour only)
- Workspace-level isolation (not shared across orgs)

**Anti-patterns that silently kill cache hits:**
- Timestamps in cached content ("Current time: 2026-07-28T14:32:15Z")
- Per-user data in prefix ("You are helping Jane who works at Acme")
- Inconsistent whitespace in prompt builder
- Randomized JSON key order (Swift, Go)

## Example

Caching a system prompt and tool definitions for an agentic loop:
```python
import anthropic

client = anthropic.Anthropic()

system_prompt = """
You are a code assistant. You can read files, run tests, and suggest changes.
[... large instruction set ...]
"""

tools = [
    {
        "name": "read_file",
        "description": "Read a file",
        "input_schema": {...}
    },
    # ... many more tools ...
]

# First request: writes cache
response1 = client.messages.create(
    model="claude-opus-5",
    max_tokens=2048,
    cache_control={"type": "ephemeral"},  # Caches system + tools
    system=system_prompt,
    tools=tools,
    messages=[{"role": "user", "content": "Find the bug in app.py"}]
)
print(f"First call — wrote {response1.usage.cache_creation_input_tokens} tokens to cache")

# Follow-up: reads from cache (~10% cost)
response2 = client.messages.create(
    model="claude-opus-5",
    max_tokens=2048,
    cache_control={"type": "ephemeral"},  # Same prefix hits cache
    system=system_prompt,
    tools=tools,
    messages=[{"role": "user", "content": "Now check tests.py"}]
)
print(f"Second call — read {response2.usage.cache_read_input_tokens} tokens from cache")
```

## Notes & links

- **Breakpoint placement:** Place `cache_control` on the last block that's identical across requests. Moving it earlier means the later (changing) content isn't cached but still uses tokens. Moving it to a changing block (timestamps, user messages) means you pay write cost every request.
- **Verification:** Check `usage.cache_creation_input_tokens` and `cache_read_input_tokens` to confirm caching is working.
- **Pre-warming:** Load cache before real traffic with a dummy request (`max_tokens: 0`) to write the prefix and return immediately.
- For RAG workflows, consider combining caching with retrieval on demand to keep queries fast without over-caching intermediate results.
- **Break-even & worked cost** (2,500-token system prompt reused across 10 requests):

  | | Cost |
  |---|---|
  | Without caching | 2500 × 10 × input rate |
  | With caching | write (2500 × 1.25) + reads (2500 × 9 × 0.1) |
  | **Savings** | **~90–95%** |

  Break-even is at 2 calls; everything after is pure savings.
- **Stacking discounts:** caching + the Batch API stack — on Haiku that compounds to ~20× cheaper than uncached on-demand.
- Cache your large CLAUDE.md / system prompt above the breakpoint and keep dynamic content below it — see [[instruction-hierarchy-layering]].
