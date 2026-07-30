---
id: structured-outputs-api
title: Structured outputs for guaranteed schema compliance
category: prompting
ecosystems: [claude-api, claude-sdk]
problem: Prompt-only JSON constraints allow malformed output, invalid fields, type errors
maturity: established
confidence: verified
effort_to_adopt: medium
works_with: []
supersedes: []
sources:
  - {url: "https://platform.claude.com/docs/en/build-with-claude/structured-outputs", kind: docs, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Even careful prompting ("return JSON," "required fields: name, email") can produce invalid JSON, missing fields, wrong types, or schema violations. Downstream code then needs error handling and retries, adding latency and complexity.

## How it works

Structured outputs use **constrained decoding** to enforce schema at token-generation level, not via prompt guidance. You define a JSON schema (via JSON Schema or SDK types like Pydantic, Zod), and Claude's output is mathematically guaranteed to match that schema. Invalid tokens are never generated.

Unlike prompt engineering (which *asks* for a format), structured outputs *enforce* it. The API automatically injects a system prompt explaining the schema, so the model understands the constraints and cooperates.

## Setup

### Via Claude API (JSON Schema)

```json
{
  "model": "claude-opus-5",
  "max_tokens": 1024,
  "messages": [{"role": "user", "content": "Extract contact info from this email..."}],
  "output_config": {
    "format": {
      "type": "json_schema",
      "schema": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "email": {"type": "string", "format": "email"},
          "phone": {"type": "string"}
        },
        "required": ["name", "email"]
      }
    }
  }
}
```

### Via SDK (Pydantic / Zod)

**Python:**
```python
from pydantic import BaseModel, EmailStr

class ContactInfo(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None

response = client.messages.parse(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Extract contact info..."}],
    output_format=ContactInfo
)

print(response.parsed_output)  # Type-safe, guaranteed valid
```

**TypeScript:**
```typescript
import { z } from "zod";

const ContactInfo = z.object({
  name: z.string(),
  email: z.string().email(),
  phone: z.string().optional()
});

const response = await client.messages.parse({
  model: "claude-opus-5",
  max_tokens: 1024,
  messages: [{ role: "user", content: "Extract contact info..." }],
  output_format: ContactInfo
});

console.log(response.parsed_output); // Type-safe
```

## When to use / when NOT

**Use structured outputs when:**
- Output must be valid JSON matching a schema
- Downstream code parses output programmatically
- Invalid output breaks your system
- You need type safety (SDK usage)

**Use prompt engineering when:**
- Output is for human consumption (reports, explanations)
- Schema flexibility is acceptable
- You want natural variation in phrasing

**You can combine both:** Use structured outputs to guarantee format, then prompt to influence *what* the output says (tone, detail level, etc.).

## Tradeoffs

- **Pro:** Guaranteed valid JSON; no `JSON.parse()` errors or schema violations
- **Pro:** No retries needed for format violations
- **Pro:** Type-safe if using SDK
- **Pro:** Output constraints can actually *improve* quality (model focuses on content)
- **Con:** Adds ~50-100 tokens to system prompt (cost multiplier)
- **Con:** Incompatible with citations (citing within strict JSON is hard)
- **Con:** Message prefilling not supported on last assistant turn (Claude 4.6+)
- **Con:** Requires schema definition upfront

## Example

**Task:** Extract structured data from customer support emails.

**Without structured outputs (needs error handling):**
```python
response = client.messages.create(
    model="claude-opus-5",
    messages=[{"role": "user", "content": "Extract: " + email}],
    system="Return valid JSON with fields: issue, priority, customer_id"
)

try:
    data = json.loads(response.content[0].text)
    # Still might be missing fields or wrong types
except json.JSONDecodeError:
    # Retry
```

**With structured outputs (guaranteed valid):**
```python
class SupportTicket(BaseModel):
    issue: str
    priority: Literal["low", "medium", "high"]
    customer_id: int

response = client.messages.parse(
    model="claude-opus-5",
    messages=[{"role": "user", "content": "Extract: " + email}],
    output_format=SupportTicket
)

# response.parsed_output is valid SupportTicket object, no try/except needed
print(response.parsed_output.priority)  # Type-safe access
```

Result: No error handling, type-safe, first-call success.

## Notes & links

- **Model availability:** Supported on Claude 4.5 and later models (including Opus 5, Sonnet 5, Haiku 4.5, and their Bedrock equivalents).
- **Schema constraints:** Requires `additionalProperties: false` on objects; does not support string length or numeric range constraints (use validation after parsing if needed).
- **Retry logic:** SDK provides automatic validation & retry; if max retries exhausted, returns error rather than invalid JSON.
- **Cost:** Output token cost unaffected; input tokens slightly higher due to injected schema prompt.
- Complement with [[few-shot-examples]] to guide *content* while structured outputs enforce *format*.
