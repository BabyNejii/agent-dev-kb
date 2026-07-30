---
id: xml-structured-prompting
title: XML tags for unambiguous prompt structure
category: prompting
ecosystems: [claude-api, claude-sdk, claude-code]
problem: Long prompts mixing instructions, context, examples, and inputs cause misinterpretation
maturity: established
confidence: verified
effort_to_adopt: low
works_with: [few-shot-examples]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags", kind: docs, date: "2026-07-28"}
  - {url: "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices", kind: docs, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Unstructured prompts with mixed instructions, context, examples, and variable data cause Claude to misinterpret role of each section, leading to hallucinations, format errors, or lost nuance.

## How it works

XML-style tags (`<instructions>`, `<context>`, `<example>`, `<document>`, etc.) create unambiguous boundaries that Claude parses more reliably than markdown headers or plain text. Claude was specifically designed to handle XML-structured input. The model can distinguish sections and apply appropriate processing to each.

Benefits: Reduced parsing errors, better format consistency, clearer variable boundaries, easier prompt maintenance.

## Setup

1. **Choose consistent, descriptive tag names:**
   ```xml
   <instructions>
   Do X, then Y.
   </instructions>

   <context>
   Background on the domain...
   </context>

   <input>
   {{USER_DATA}}
   </input>
   ```

2. **Nest tags for hierarchy:**
   ```xml
   <documents>
     <document index="1">
       <source>report.pdf</source>
       <document_content>{{CONTENT}}</document_content>
     </document>
   </documents>
   ```

3. **Common patterns** (no mandated set; use names that fit your task):
   - `<task>` — what to do
   - `<instructions>` — how to do it
   - `<constraints>` — hard limits
   - `<context>` / `<background>` — domain info
   - `<documents>` / `<document>` — long-form inputs
   - `<examples>` / `<example>` — few-shot demonstrations
   - `<input>` / `<user_query>` — variable user data
   - `<output_format>` — desired output structure
   - `<reasoning>` / `<thinking>` — encourage explicit reasoning

4. **For multi-document tasks**, structure with metadata:
   ```xml
   <documents>
     <document index="1">
       <source>annual_report.pdf</source>
       <document_content>{{REPORT_TEXT}}</document_content>
     </document>
     <document index="2">
       <source>competitor_analysis.xlsx</source>
       <document_content>{{ANALYSIS_TEXT}}</document_content>
     </document>
   </documents>
   ```

## When to use / when NOT

**Use when:**
- Prompt > 500 tokens mixing multiple content types
- Queries follow long documents (30%+ quality improvement)
- Extracting from or processing structured input
- Tool-use or agentic loops (clarify role of each step)
- Code generation (structure instructions → context → examples → input)

**NOT when:**
- Simple 1-line requests (overhead outweighs benefit)
- Conversational chat (session context already clear)
- Single sentence instructions

## Tradeoffs

- **Pro:** Major clarity for complex prompts; community reports 20-40% consistency improvement, though official benchmarks vary
- **Pro:** Easier to modify/extend prompts
- **Con:** Adds verbosity (use only when complex)
- **Con:** Requires discipline to keep tag names consistent
- **Con:** Not a substitute for clear writing (still need to explain *why*)

## Example

Code generation with XML structure:

```xml
<instructions>
Create a REST API endpoint that accepts a list of user IDs and returns their profiles.
The response must be paginated and include error handling.
</instructions>

<constraints>
- Use Express.js
- Must validate input (ids must be positive integers)
- Database query must use prepared statements
- Return 400 for invalid input, 500 for server errors
</constraints>

<examples>
<example>
Input: POST /api/users/profiles?ids=1,2,3
Output: {
  "data": [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"}
  ],
  "page": 1,
  "total": 2
}
</example>
</examples>

<input>
{{USER_REQUEST}}
</input>
```

Result: Clearer structure → fewer format mismatches → working code on first try.

## Notes & links

- **XML in output:** You can ask Claude to structure its output in XML too (e.g., `<answer>` tags), which makes post-processing reliable.
- **No canonical tags:** Anthropic recommends meaningful names relevant to your context—there's no magic set.
- **Pairs with thinking:** Use `<thinking>` tags in few-shot examples; Claude generalizes that style to extended thinking blocks.
- Query position matters: put long documents at the *top*, then structured context, then query at *bottom*. This can improve quality by 30%.
- See [[few-shot-examples]] for combining XML with examples.
