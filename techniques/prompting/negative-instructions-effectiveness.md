---
id: negative-instructions-effectiveness
title: When negative instructions work (and when they fail)
category: prompting
ecosystems: [claude-code, claude-api, claude-sdk]
problem: '"Do not" instructions sometimes work, sometimes fail to prevent unwanted behavior'
maturity: established
confidence: reported
effort_to_adopt: low
works_with: []
supersedes: []
sources:
  - {url: "https://eval.16x.engineer/blog/the-pink-elephant-negative-instructions-llms-effectiveness-analysis", kind: blog, date: "2026-07-28"}
  - {url: "https://dev.to/docat0209/5-patterns-that-make-claude-code-actually-follow-your-rules-44dh", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Negative instructions ("do not," "avoid," "never") sometimes prevent Claude from misbehaving; other times they're ignored or even backfire. Developers aren't sure when negatives work or how to write them effectively.

## How it works

Claude respects well-formed negative instructions better than many LLMs, but effectiveness depends on *how* you frame them:

**Hard negatives work:** "Must not," "never," "do not," "forbidden" are treated as rules.

**Soft negatives fail:** "Try to avoid," "prefer not to," "if possible skip" are interpreted as suggestions and often ignored.

**Positive reframing is stronger:** "Always X" beats "Never do Y" because the model doesn't have to resolve a negation—it just follows the positive instruction directly.

## Setup

1. **Use hard language for critical rules:**
   ```
   WRONG:  "Try to avoid using force-push"
   RIGHT:  "Never use git push --force on shared branches"
   ```

2. **Limit negatives to 3-5 per prompt:**
   ```
   More than 5-6 negatives causes confusion and ignored constraints.
   Group related rules: "Never use hype words (disruptive, revolutionary, game-changing)"
   counts as one rule.
   ```

3. **Pair negatives with positives:**
   ```
   WEAK:   "Do not be verbose"
   STRONG: "Be concise. Write 2-3 sentences max, no preamble"
   
   The positive instruction tells the model what to DO, not what to resolve.
   ```

4. **Place critical rules at top and bottom of CLAUDE.md:**
   ```
   Recency bias: Claude gives more weight to early and final instructions.
   Put the rules you violate most often at the very top and very bottom.
   ```

5. **Test on your target models:**
   ```
   Claude, GPT-5.5, and Gemini have different compliance sensitivities.
   A constraint that works on Claude may fail on GPT or over-apply on Gemini.
   ```

## When to use / when NOT

**Use negatives (hard language) when:**
- Preventing safety/security violations (unethical behavior, secrets, malicious code)
- Enforcing firm boundaries (don't delete files, don't force-push, don't modify external systems)
- Current default behavior is wrong (Claude edits files when not asked, uses hype language, etc.)

**Use positives instead when:**
- You can describe the desired behavior clearly
- A negative would require the model to resolve a double-negative
- The rule applies to style/tone (prefer positive framing for subjective guidance)

**Don't use either when:**
- The rule is optional or context-dependent (use a suggestion or explanation instead)
- You're trying to prevent rare edge cases (focus on top issues first)

## Tradeoffs

- **Pro:** Hard negatives work reliably with Claude; better than with GPT-4o
- **Pro:** Cheap (no tokens beyond the rule itself)
- **Con:** Overuse causes ignored constraints (pile-on fatigue)
- **Con:** Risk of opposite behavior: "never be verbose" sometimes triggers overly terse, unhelpful responses
- **Con:** Different models have different compliance; test before deploying
- **Con:** "Pink elephant problem" (ironic process theory): explicitly avoiding something can make you think about it more

## Example

**Bad negatives (ignored):**
```
- Do not make new file versions
- Try to avoid using markdown
- Don't be overly cautious
```

**Good negatives (respected):**
```
- NEVER create new file versions. Always edit existing files.
- Do not use markdown formatting in responses. Use plain prose.
- Do not ask for permission for reversible local actions.
```

**Better (positives):**
```
- Make all updates in existing files whenever possible.
- Format responses as plain prose paragraphs, no markdown or bullets.
- Take reversible local actions (edits, tests) without asking; only confirm destructive actions.
```

Tested result: Flipping 10 negative rules to positive equivalents reduced rule violations by ~50%.

## Example: Real code scenario

**Task:** Agent shouldn't duplicate files when refactoring.

**Approach 1 (fails):** "Do not make new versions"
```
Result: Agent still duplicates files; instruction ignored.
```

**Approach 2 (works better):** Hard negative
```
"NEVER create new file versions. ALWAYS make all changes to existing files."
Result: Better; agent respects "always" more than "do not"
```

**Approach 3 (works best):** Positive + context
```
"Make all possible updates in existing files whenever possible.
Avoid creating intermediate copies or helper files.
Refactoring should consolidate, not proliferate, files."
Result: Agent consistently edits in-place; understands the *why*.
```

## Notes & links

- **Explain the rationale:** When possible, explain *why* the rule exists. Claude makes better judgments at edge cases when it understands the intent, not just the rule.
- **Safety rules are exempt:** Negatives for ethical/safety guardrails ("never create malicious code," "never share credentials") work reliably even as negatives; the model is trained to respect them.
- **Placement matters:** Top and bottom of CLAUDE.md get more weight due to recency bias.
- **Model-specific:** Claude respects negatives well compared to other models; don't assume your prompt works identically on GPT-5.5 or Gemini.
- Combine with [[instruction-hierarchy-layering]] to organize persistent vs request-specific negatives.
