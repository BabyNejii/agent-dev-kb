---
id: lost-in-middle-mitigation
title: Lost-in-middle mitigation — reordering context to preserve attention on critical tokens
category: context
ecosystems: [claude-api, claude-sdk, claude-code, generic]
problem: 'Models lose focus on tokens in the middle of long contexts (U-shaped attention curve); critical information buried in the middle of 50K+ token contexts gets overlooked'
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [context-compaction-beta, agentic-rag-tool-based-retrieval]
supersedes: []
sources:
  - {url: "https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", kind: github, date: 2026-07-30}
  - {url: "https://github.com/Meirtz/Awesome-Context-Engineering", kind: github, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

When contexts exceed ~20K tokens, language models exhibit U-shaped attention: they pay strong attention to tokens at the **beginning and end** of the context, but lose focus on the **middle**. This "lost-in-middle" phenomenon causes critical information buried in the middle of a long context to be overlooked, even if it should be crucial to the task. In large codebases, long conversations, or extensive reference materials, the most important details (the bug, the API contract, the architecture decision) often end up in the lost-middle zone and are ignored by the model.

## How it works

Several strategies mitigate lost-in-middle:

**1. Reorder to surface criticality**
- Move the most important context to the **start** (after task instructions).
- Move secondary/reference material to the **end**.
- Push rarely-needed context (legacy code, deprecated APIs) to the middle.
- Example: In a large codebase, put core types and high-call-frequency functions first; utility code and deprecated methods last.

**2. Interleave critical tokens throughout**
- Don't cluster critical information in one section; scatter key details across the context.
- Repeat critical constraints or goal statements at multiple points.
- Example: Repeat the error message and constraint at the start, middle, and end rather than just once in the middle.

**3. Reduce context length** (preemptive)
- Use [[context-compaction-beta]] or [[agentic-rag-tool-based-retrieval]] to keep context under 20K tokens, avoiding the middle-loss zone entirely.
- Better to have 10K high-signal tokens than 50K with buried needles.

**4. Use retrieval to raise signal**
- Instead of loading all context, use agents to **retrieve** the most relevant pieces on-demand.
- Agentic RAG: agents call tools to search, filter, and assemble context dynamically, keeping the main context tight.

## Setup

**For code/codebase contexts:**

1. Identify critical elements:
   - Core types and data structures (must be visible)
   - High-traffic functions (must be visible)
   - Recent/active code sections
   - Current task or bug description

2. Structure context:
   ```
   [Task / Bug description] ← critical, goes first
   [Core types and interfaces]
   [Most-called functions]
   [Architecture notes]
   [Recent changes / test results]
   
   [Utility functions and helpers]
   [Deprecated code]
   [Legacy reference material]
   ```

3. For very large contexts (>30K), prefer agentic retrieval:
   ```
   Agent instructions → [tool: search for function X]
   → [tool: retrieve tests for module Y]
   → [tool: fetch architecture ADR Z]
   Context never gets bloated; agent assembles pieces on-demand.
   ```

**For conversation/conversation contexts:**

4. Use [[context-compaction-beta]]:
   - Summarize old messages; keep recent messages in full.
   - Periodically compact conversation history.
   - Repeat the current task/goal statement before each new request.

5. For very long conversations, archive old context:
   ```
   [Current task / goal] ← repeat here
   [Recent messages: last 5 exchanges] ← full detail
   [Older messages: summary] ← condensed
   [Tools/APIs still in use]
   ```

## When to use / when NOT

**Use when:**
- Context exceeds ~20K tokens and you've observed quality degradation ("model ignores middle sections").
- Critical information is scattered across long documents/codebases.
- You're running long agentic loops (conversation + output) where middle-loss compounds.
- You can't reduce context further (e.g., full codebase must be present).

**Don't use when:**
- Context is short (< 10K tokens); middle-loss effect is negligible.
- Latency is critical; reordering/retrieval adds processing time.
- Context order is semantically important (e.g., a narrative that must be read sequentially).
- You have no ability to modify context structure (reading-only scenarios).

## Tradeoffs

| Benefit | Cost |
|---------|------|
| Recovers quality when using long contexts | Reordering adds preprocessing time; requires understanding what's "critical" |
| Allows keeping full context instead of lossy summarization | May distort natural reading order or narrative flow |
| Scales with agentic retrieval rather than static reordering | Retrieval adds latency per lookup; more API calls |
| Complements compression: both reduce effective middle-loss risk | Requires experimentation to find optimal reordering |

## Example

**Scenario: Debugging a 500-line class in a large codebase**

*Without lost-in-middle mitigation:*
```
Context: [500 lines of class code] + [100 lines of related classes] + [test file]
= 30K tokens, middle-loss zone active
Model reads: beginning and end, but middle (where the bug is) gets low attention
Result: Model misses the bug that's in the middle of the class
```

*With reordering:*
```
Context:
1. [Task: "Find bug in payment processing"]
2. [Relevant test that fails]
3. [Class methods in order of call frequency]
4. [The actual bug region: payment calculation method]
5. [Related utility code]
6. [Legacy/deprecated methods]

Result: Model focuses on critical methods (start), can reason about the bug
```

*With agentic retrieval (best for very large codebase):*
```
Agent gets:
- Task description
- Tool: "search_codebase(pattern)"
- Tool: "get_file_around_line(file, line, window=20)"
- Tool: "find_tests_for_function(fn_name)"

Agent: "I'll search for payment processing, fetch that function, get its tests"
Context remains tight (~8K); agent assembles exactly what's needed
Result: No middle-loss; high signal-to-noise ratio
```

## Notes & links

- The U-shaped attention curve is an empirical observation from studying how transformers allocate attention over long contexts. See work on "attention entropy" and "position bias" in LLM research.
- Related to [[context-compaction-beta]]: both address quality issues at scale. Compaction reduces size; reordering preserves important content visibility. Often used together.
- Related to [[agentic-rag-tool-based-retrieval]]: retrieval is the "nuclear option" for lost-in-middle — avoid it by keeping context short and reordered. Use retrieval when you can't compress further.
- Applicable across Claude models and other transformers; effects are more pronounced in longer contexts (> 30K tokens).
