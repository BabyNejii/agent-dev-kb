---
id: api-hallucination-prevention
title: Preventing Claude from inventing non-existent APIs
category: eval
ecosystems: [claude-code, claude-api]
problem: Claude generates code calling methods that don't exist, especially for unfamiliar libraries
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [schema-validation-gates]
supersedes: []
sources:
  - {url: "https://docs.bswen.com/blog/2026-03-22-claude-code-api-hallucination-fix/", kind: blog, date: "2026-03-22"}
  - {url: "https://www.developersdigest.tech/blog/tool-use-claude-api-production-patterns", kind: blog, date: "2026-02-15"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Claude sometimes generates code calling methods like `array.unique()` (JavaScript, doesn't exist) or `dict.get_values()` (Python, doesn't exist). The model is pattern-matching on learned code, not consulting actual API documentation. For unfamiliar libraries, hallucination rates spike.

## How it works

**Root cause:** Claude doesn't have real-time knowledge of your specific APIs or libraries. It produces plausible output based on training patterns.

**The fix:** Multiple layers of specificity and grounding:

1. **Supply concrete API signatures:** Rather than asking "write code to fetch users," provide the exact methods:
   ```
   Available methods:
   - database.find_users(role: str, limit: int) -> List[User]
   - database.count_users(role: str) -> int
   
   Do NOT invent other methods.
   ```

2. **Use MCP for live validation:** MCP servers provide real-time tool schemas and documentation, so Claude can verify methods exist before calling them.

3. **Verification checkpoints:** After generation, have Claude list every external call and confirm each against documentation.

4. **Scope requests narrowly:** Large requests invite hallucination. "Write code that fetches and transforms users" is vaguer than "call database.find_users() and map to JSON."

## Setup

1. **Explicit method list in system prompt or CLAUDE.md:**
```
Available database methods:
- find_users(filters: dict, limit: int = 100) -> List[dict]
- find_organizations(id: str) -> dict | None
- create_audit_log(event: str, user_id: str) -> bool

CONSTRAINT: Use only these methods. Do not call find_user (singular) or any method not listed.
```

2. **Verification checklist for Claude after code generation:**
```
After writing code, perform this check:
1. List every external API call in your code
2. Verify each call against the provided method list
3. If any call is not in the list, rewrite it or flag as uncertain
4. Confirm parameter types match the signature
```

3. **Use MCP for live discovery (optional but recommended):**
```python
# CLAUDE.md or project config
[mcp-servers]
database = "path/to/database-mcp-server"
# Claude can now introspect real method signatures

# In skill or agent prompt
"Use the database MCP server to explore available methods before writing code."
```

4. **Post-generation static check:**
```python
def verify_api_calls(code_str, available_apis):
    """Extract all method calls and verify they're documented."""
    import ast
    tree = ast.parse(code_str)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                method = f"{node.func.value.id}.{node.func.attr}"
                if method not in available_apis:
                    return False, f"Hallucinated: {method}"
    return True, None
```

## When to use / when NOT

**Use when:**
- Calling unfamiliar libraries or internal APIs
- You have a small, stable set of allowed methods
- Preventing hallucination is more important than flexibility

**NOT when:**
- Building with standard libraries (less hallucination risk)
- APIs are dynamic and frequently change
- Broad exploration is needed (too restrictive)

## Tradeoffs

**Pros:**
- Simple to implement (just documentation)
- Catches 80–90% of hallucinations
- Works with Claude without changes to agent architecture

**Cons:**
- Requires updating method lists when APIs change
- Doesn't catch logical errors (wrong method for the task)
- Only works if the actual methods are pre-supplied

## Example

**Without prevention:**
```
User: "Write code to get all users with role='admin'."

Claude output (hallucinates):
users = db.get_all_users(role='admin')  # Method doesn't exist
```

**With prevention:**

Provide documented methods:
```
database.find_users(filters: dict, limit: int) -> List[dict]
database.find_organizations(id: str) -> dict | None
```

Instruction: "Do not call any method not listed above."

Claude output:
```python
users = database.find_users(filters={'role': 'admin'})  # Correct
```

## Notes & links

- One team reports 87% reduction in hallucinated API calls by combining explicit method lists + verification checkpoints.
- The verification checklist takes 30s and saves hours of debugging.
- For internal APIs, store authoritative method signatures in a skill or `.md` that Claude can reference.
- Combine with [[schema-validation-gates]] for runtime safety: if a tool call has an unknown method, reject it before execution.
