---
id: few-shot-examples
title: Few-shot examples anchor format and behavior
category: prompting
ecosystems: [claude-api, claude-sdk, claude-code]
problem: Instructions alone don't reliably guide output format, tone, or edge-case handling
maturity: established
confidence: verified
effort_to_adopt: low
works_with: [xml-structured-prompting]
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices", kind: docs, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Text instructions ("return JSON," "be concise," "use this tone") don't always produce consistent output. Claude infers from examples more reliably than from description.

## How it works

One or more worked examples (input-output pairs) show Claude exactly what you want, not just describe it. Because autoregressive models pattern-match on what they've seen, few examples anchor behavior far more effectively than instruction text alone. Effectiveness rated 9/10 across task types.

## Setup

1. **Start with 1 example, scale to 3-5:**
   - 1 example (one-shot) often sufficient for straightforward tasks
   - 3-5 examples (few-shot) needed for complex tasks, edge cases, consistency

2. **Wrap examples in tags for clarity:**
   ```xml
   <examples>
     <example>
       <input>Extract the name from: "John Smith, age 30"</input>
       <output>{"name": "John Smith"}</output>
     </example>
     <example>
       <input>Extract the name from: "Dr. Jane Doe (PhD)"</input>
       <output>{"name": "Jane Doe"}</output>
     </example>
   </examples>
   ```

3. **Make examples:**
   - **Relevant:** Mirror your actual use case (if extracting names from emails, show email-like inputs)
   - **Diverse:** Cover edge cases and vary enough Claude doesn't pattern-match on wrong details (include titles, multiple names, etc.)
   - **Structured:** Use consistent format across examples

4. **Combine with reasoning** (especially powerful with thinking):
   ```xml
   <example>
     <input>Is "disrupting the market" in this text?</input>
     <thinking>
     "Disrupting" is marketing hype. The rule is to flag hype language. This sentence uses hype.
     </thinking>
     <output>Yes, contains hype language</output>
   </example>
   ```
   Claude generalizes the reasoning pattern to its own thinking blocks.

## When to use / when NOT

**Use when:**
- Output format is specific (JSON schema, markdown structure, code)
- Tone or style matters (formal vs casual, verbose vs terse)
- Edge cases need consistent handling
- Task requires multi-step reasoning
- Instructions alone have failed in testing

**NOT when:**
- Simple classification (yes/no, 1-5 scale)
- Open-ended creative writing
- Task is self-explanatory

## Tradeoffs

- **Pro:** Dramatically improves consistency; shows > tells
- **Pro:** Captures nuance (tone, format, edge case handling) better than text
- **Con:** Adds tokens to every request (overhead if overused)
- **Con:** Requires quality examples (bad examples teach bad patterns)
- **Con:** Newer models (Claude 4.x) are *very* sensitive to example details; ensure examples don't demonstrate patterns you want to avoid

## Example

**Task:** Classify product reviews as positive/negative, capturing nuance.

**Without examples (unreliable output format):**
```
Classify this review as positive or negative: "Good product, but shipping took forever."
```
Claude might output: "mixed" or "positive/negative" or a paragraph.

**With examples (consistent format + edge case handling):**
```xml
<examples>
  <example>
    <input>"Great quality! Arrived quickly."</input>
    <output>positive</output>
  </example>
  <example>
    <input>"Good product, but shipping took forever."</input>
    <output>mixed (product positive, experience negative)</output>
  </example>
  <example>
    <input>"Broke after 2 days. Terrible."</input>
    <output>negative</output>
  </example>
</examples>

Classify: "Good product, but shipping took forever."
```
Claude now outputs: `mixed (product positive, experience negative)` consistently.

## Notes & links

- **Ordering matters:** Recent examples (closer to end) have more weight; put strongest/most typical examples near input.
- **Evaluation:** Ask Claude to evaluate your examples for relevance and diversity; it can generate additional ones.
- **Avoid hallucination:** Be careful with newer models—they learn from example details, so avoid patterns you don't want generalized (e.g., don't show an example of a "clever" shortcut if you want by-the-book solutions).
- **With thinking:** Multishot examples + thinking tags let you show reasoning patterns; Claude's thinking style will follow your examples.
- See [[xml-structured-prompting]] for combining with tags for clarity.
