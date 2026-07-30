---
id: codebase-agent-optimization
title: Structural codebase optimization for agent reasoning efficiency
category: codebase-ops
ecosystems: [claude-code, claude-sdk, generic]
problem: "Agent reasoning degrades on codebases designed for humans; scattered symbols, deep nesting, and missing indices force agents to waste tokens on navigation and rediscovery"
maturity: emerging
confidence: reported
effort_to_adopt: high
works_with: [code-summary-meta-rag, hybrid-codemod-agent-refactoring, safe-monolith-decomposition]
supersedes: []
sources:
  - {url: "https://github.com/nibzard/awesome-agentic-patterns#tool-use--environment", kind: github, date: 2026-07-30}
  - {url: "https://github.com/ai-boost/awesome-harness-engineering#design-primitives-1", kind: github, date: 2026-07-30}
added: 2026-07-30
updated: 2026-07-30
---

## Problem

Human-friendly code layout (flat file organization, contextual naming, visual structure) does not minimize agent navigation cost. Agents waste tokens:

- **Rediscovering symbols:** The same function appears in 3 places. Agent searches for it, reads all 3, wonders which is canonical.
- **Scanning deep hierarchies:** `src/features/payment/handlers/validation/schema/rules/business/...` requires many reads before the agent understands "where is the schema?"
- **Accumulating context from scattered definitions:** A type is defined in one file, extended in another, mocked in a test helper, copied in docs—agent reads all 4 to be safe.
- **No semantic index:** Agent cannot ask "which functions touch this database table?" and must grep and infer.

Result: Agent task that should cost 50K tokens costs 200K+ due to navigation overhead.

## How it works

**Symbol indexing:** Create a discoverable, unambiguous registry of key definitions (functions, types, classes, tables, APIs). Agent queries the index first, reducing exploratory reads.

**Semantic flattening:** Move related definitions into the same file or well-named directory, reducing the number of hops to understand a concept.

**API-first documentation:** Design APIs and schemas so agents can infer behavior without reading implementation (clear parameter names, type annotations, docstrings).

**Reduced nesting depth:** Prefer `src/handlers/`, `src/models/`, `src/utils/` over `src/features/payment/handlers/validation/v2/...`.

**Agent-scannable logs and errors:** Error messages should include the relevant file path and line number; logs should include context tags (transaction ID, feature flag, version) so agents can trace execution.

## Setup

1. **Build a symbol index:**
   ```python
   # index.json
   {
     "functions": [
       {"name": "charge_card", "file": "src/payment/charge.py", "line": 42, "signature": "charge_card(amount: int, card_token: str) -> Receipt"},
       {"name": "create_invoice", "file": "src/billing/invoice.py", "line": 88, "signature": "create_invoice(customer_id: str, items: list) -> Invoice"}
     ],
     "types": [
       {"name": "Receipt", "file": "src/payment/models.py", "line": 12},
       {"name": "Invoice", "file": "src/billing/models.py", "line": 5}
     ],
     "tables": [
       {"name": "payments", "columns": ["id", "customer_id", "amount", "status"], "file": "src/db/schema.sql"}
     ]
   }
   ```

2. **Provide an MCP or CLI tool for agent lookup:**
   ```bash
   agent-find-symbol payment_handlers  # → src/payment/handlers.py
   agent-list-types payment            # → Receipt, Invoice, Transaction
   agent-search-usage charge_card      # → files that call charge_card
   ```

3. **Enforce shallow nesting:**
   - Max depth: 4 levels (`src/<domain>/<subdomain>/<type>/<file>`)
   - Rationale: Agent can infer location from path alone

4. **Standardize error messages:**
   ```
   Error: ValidationError in src/payment/validators.py:73
   Schema: payment_schema (see src/payment/models.py:12)
   Expected: amount >= 100, got 50
   ```

5. **Add inline type hints and docstrings:**
   ```python
   def charge_card(amount: int, card_token: str) -> Receipt:
       """
       Charge a credit card and return a receipt.
       
       Args:
           amount: cents to charge (must be >= 100)
           card_token: Stripe token from tokenize_card()
           
       Returns:
           Receipt with status, transaction_id, timestamp.
           
       Raises:
           InsufficientFunds: if card balance < amount
           InvalidToken: if token expired or revoked
       
       Side effects: writes to payments table, triggers webhook
       """
   ```

## When to use / when NOT

**Use if:**
- Agent tasks require exploring unknown codebases
- Token budget is tight; minimizing context is critical
- Codebase is growing and symbol lookup is becoming a bottleneck
- Agent frequently re-discovers the same functions

**Do NOT use if:**
- Codebase is small (<10k lines); overhead of indexing > savings
- Symbol names are truly unique and unambiguous
- Agent mostly operates within a single well-known module
- Dynamic reflection is already in place (agents can call help() or inspect runtime)

## Tradeoffs

| Pro | Con |
|---|---|
| Reduced token cost for large codebases | Ongoing maintenance: index must stay in sync with code |
| Faster agent exploration and learning | Shallow nesting can feel restrictive for domain modeling |
| Deterministic navigation (no ambiguity) | Refactoring becomes harder (must update index and docs) |
| Compound benefit: agents teach humans about structure | Initial cost: restructuring existing codebase is expensive |

## Example

**Before optimization:**
```
src/
  features/
    payment/
      handlers/
        validation/
          schema/
            rules/
              business/
                charge_rules.py (←  where is this?)
          regex/
            card_patterns.py
```

Agent searches `grep -r "charge_card"` → reads 8 files, context balloons.

**After optimization:**
```
src/
  payment/
    charge.py          (main logic)
    models.py          (types: Receipt, Invoice)
    validators.py      (validation rules)
    handlers.py        (HTTP endpoints)
  index.json          (symbol registry)
```

Agent calls `agent-find-symbol charge_card` → `src/payment/charge.py:42` → reads 1 file.

## Notes & links

- **Stripe's finding (harness-engineering):** "Agents ignore passive docs; guidance must sit in loaded context—skill files, error messages, CLI prompts—or it effectively didn't exist."
- **Token Savior, codebase-memory-mcp, semble:** implementations of symbol indexing that report
  large reductions in active tokens. The specific figures are self-reported by each project and
  reached us third-hand via a link list, so they are omitted here deliberately — measure on your
  own repo rather than trusting a headline number.
- **Agent-First Tool Discovery (nibzard):** Related pattern focusing on tool discoverability, not symbol indexing.
- **Related entries:** [[code-summary-meta-rag]] (summarizing large codebases), [[hybrid-codemod-agent-refactoring]] (large-scale refactoring), [[safe-monolith-decomposition]] (structural changes).
