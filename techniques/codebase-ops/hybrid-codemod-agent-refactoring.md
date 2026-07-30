---
id: hybrid-codemod-agent-refactoring
title: Hybrid Codemod + Agent Approach for Large-Scale Refactoring
category: codebase-ops
ecosystems: [claude-code, claude-sdk]
problem: Pure agent approaches burn tokens/cost on repetitive file edits; pure codemods lack contextual reasoning
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: []
supersedes: []
sources:
  - {url: "https://codemod.com/blog/npx-codemod-ai", kind: blog, date: "2026-07-28"}
  - {url: "https://medium.com/qonto-way/ai-driven-refactoring-in-large-scale-migrations-strategies-and-techniques-fcdb9b5116c6", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Large codebases can't afford pure agent approaches — having an agent edit every file means thousands of LLM calls and millions of tokens. But dumb text-based find-and-replace misses contextual edge cases. The tension: agents are expensive but thorough; codemods are cheap but brittle.

## How it works

The hybrid pattern delegates work by domain: the agent reasons about *what* to change and builds a deterministic transformation (codemod), then the codemod handles the *doing* across the entire repository in seconds. The agent writes a compiler-aware AST-based transformation (e.g., jscodeshift for JavaScript, Strands for multi-language) that the agent validates with tests. The result: reliable, low-cost, repeatable.

**Flow:**
1. Agent analyzes the codebase and understands the refactoring goal
2. Agent generates or authors a codemod script (AST-based, deterministic)
3. Codemod scans the entire repo and applies the transformation uniformly
4. Agent validates the result with tests and reports changes

## Setup

**Choose your codemod tool** based on language:
- **JavaScript/TypeScript:** jscodeshift or Codemod's platform
- **Multi-language:** Codemod.com (AI-powered), Strands agents
- **Python:** Libcst or custom AST scripts
- **General:** Codemod CLI for AST-aware transformations

**Agentic codemod generation:**
```
Prompt Claude to:
1. Analyze the old API or pattern across sample files
2. Write the AST transformation script (jscodeshift visitor pattern)
3. Test it on a sample file to verify correctness
4. Provide the script as the output
```

**Then run the generated codemod:**
```bash
npx jscodeshift -t <generated-codemod.js> --parser=ts src/
```

**Validation loop:**
- Run the full test suite after codemod execution
- Have the agent compare before/after diffs
- Commit the changes with a structured message

## When to use / when NOT

**Use when:**
- Refactoring affects hundreds or thousands of files
- The transformation is deterministic (rename, migrate API, update pattern)
- You've already solved the transform once and need to replay it
- Cost or latency are concerns

**Don't use when:**
- The change requires understanding business logic in each file
- Edge cases are numerous and context-dependent
- The codebase is small (single agent pass is faster)
- The transformation requires back-and-forth reasoning

## Tradeoffs

**Pros:**
- Reduces token usage by up to 90% vs. pure agent approach
- Deterministic, repeatable, auditable transformations
- Fast execution (codemods scan entire repos in seconds)
- Results can be version-controlled and reviewed as a single diff

**Cons:**
- Upfront effort to build the codemod (agent-assisted, but not free)
- AST-based transformations have a learning curve
- Edge cases still need human judgment or additional agent passes
- Language-specific (must choose the right tool for each language)

## Example

**Scenario:** Migrate React 17 prop syntax to React 18 across a 50k-file codebase.

**Agent task:**
```
Read sample React components and understand:
1. Current prop destructuring patterns
2. New React.FC syntax requirements
3. Hooks changes (useEffect deps, etc.)

Write a jscodeshift codemod that:
- Converts `React.FC<Props>` to function syntax
- Updates useEffect dependency arrays per new rules
- Handles edge cases in the sample files

Test the codemod on 2-3 sample files and verify the output matches expected transformations.
```

**Agent output:** A jscodeshift transform script (`react-17-to-18.js`)

**Human runs:**
```bash
npx jscodeshift -t react-17-to-18.js --parser=tsx src/
npm test
git diff --stat
```

**Result:** Thousands of files migrated, all changes auditable in one PR.

## Notes & links

- **Qonto case study:** Paired codemod + Claude for Ember→React migration, combining deterministic rewiring with interactive LLM refinement
- **Codemod.com:** Platform that adds AI reasoning to codemod execution, giving agents compiler-aware code intelligence
- **Trade-off research:** Academic work shows agentic refactoring without structural constraints tends to tangled patches; hybrid approaches keep modifications localized and verifiable
