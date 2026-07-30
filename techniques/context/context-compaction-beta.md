---
id: context-compaction-beta
title: Context compaction for long-running agent sessions
category: context
ecosystems: [claude-api, claude-code]
problem: Long conversations and multi-turn agentic loops accumulate history that pushes toward context window limits; users can't continue without manual intervention
maturity: experimental
confidence: reported
effort_to_adopt: low
works_with: [prompt-caching-with-claude-api]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/build-with-claude/context-windows", kind: docs, date: "2026-07-28"}
  - {url: "https://hidekazu-konishi.com/entry/anthropic_claude_api_prompt_caching_and_token_efficiency.html", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Long agent sessions accumulate conversation history, tool results, and intermediate findings. Once the conversation approaches context window limits, the agent can't continue without manual pruning or session restart. This breaks agentic workflows that should run for hours, and forces the user to choose between losing context and losing productivity.

## How it works

Context compaction (beta, header `compact-2026-01-12`) server-side condenses conversation history into a summary so the session can continue. The API maintains the conversation's semantic meaning while reducing token count, typically compacting earlier turns into a single condensed block.

When enabled, the model can request compaction, or you can trigger it explicitly when approaching limits. The compacted history occupies fewer tokens, freeing space for fresh context and responses.

**Important:** Compaction is applied to conversation history, not to the system prompt or CLAUDE.md files. Those persist and reload from disk.

## Setup

**Enable compaction header (API):**
```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=2048,
    system="You are a helpful coding assistant.",
    messages=[...],
    extra_headers={
        "anthropic-beta": "compact-2026-01-12"
    }
)
```

**Manual vs. automatic:**
- **Automatic:** Model requests compaction when it detects approaching limits
- **Manual:** You explicitly request compaction via `/compact` in Claude Code or by calling the API

**After compaction:**
- Conversation history is summarized
- Project-root CLAUDE.md is re-read from disk and re-injected
- Nested CLAUDE.md files reload on-demand when Claude reads those files
- Session continues with freed token space

## When to use / when NOT

**Use compaction for:**
- Long agentic sessions (hours-long, many turns)
- Multi-step tasks with large intermediate results
- Batch processing workflows
- Sessions approaching context window limits

**NOT for:**
- Short conversations (few turns)
- Cases where exact conversation history matters (compliance, audits)
- Real-time applications (introduces latency)
- Prompts under 50K tokens (margin to limits is safe)

## Tradeoffs

**Strengths:**
- Extends long sessions without manual intervention
- Preserves semantic meaning of prior conversation
- Allows sessions to outlive a single context window
- Frees space for fresh context and reasoning

**Weaknesses:**
- Beta feature—behavior may change
- Summarization loses some detail
- Adds latency (server-side processing)
- Exact earlier conversation irretrievable (summarized)
- CLAUDE.md reload doesn't cover nested files in subdirectories

**When NOT ideal:**
- Sessions needing verbatim prior conversation (rare)
- Very latency-sensitive paths
- Conversations with sensitive context that shouldn't be summarized

## Example

**Long-running multi-step task:**

```python
# Session 1: Code analysis starts
turns = []
for file in large_file_list:
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=2048,
        extra_headers={"anthropic-beta": "compact-2026-01-12"},
        messages=turns
    )
    turns.append({"role": "user", "content": f"Analyze {file}"})
    turns.append({"role": "assistant", "content": response.content[0].text})

# After 50+ turns, approaching limits
# Compaction triggers automatically or on request
# Conversation compacted server-side
# Session continues with cleared token space

# Session resumes
response = client.messages.create(
    ...
    messages=turns  # Compacted summary + latest few turns
)
```

**Claude Code session lifecycle:**
```
Session 1: Start analyzing large codebase
  - /doctor → suggests improvements (fills context)
  - Edit 5 files → each edit adds to history
  - Run 10 tests → each result logged
  
  After 20-30 turns, tokens near 150K / 200K
  
Automatic: Claude requests compaction
  - Earlier turns (analysis, edits 1-3) → summarized
  - Recent turns (edits 4-5, tests) → kept in full
  - CLAUDE.md reloaded from disk
  
Session continues: 50K tokens freed
  - Edit remaining files
  - Run final verification
  - Synthesize results
```

## Notes & links

- **CLAUDE.md persistence:** Project-root CLAUDE.md always survives compaction and is re-injected. Nested CLAUDE.md in subdirectories is **not** automatically re-loaded; they reload on-demand when Claude reads matching files.
- **Auto-memory:** Auto memory files (MEMORY.md) are not affected by compaction and remain available on-demand.
- **Tradeoff analysis:** Compaction trades exact history for continued progress. Acceptable for agentic/exploratory work, less ideal for transactions or compliance-critical workflows.
- **Batch API alternative:** For batch processing, use the Batch API instead—it runs off-peak and avoids token limit constraints through job queueing.
- **Migration path:** When migrating sessions between models, rebaseline token counts; different models tokenize differently.

See also: [[prompt-caching-with-claude-api]], [[claude-md-persistent-memory]], [[mcp-code-api-over-tools]]
