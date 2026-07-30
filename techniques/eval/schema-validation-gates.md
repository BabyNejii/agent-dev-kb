---
id: schema-validation-gates
title: Schema validation and deterministic checks as first-line verification gates
category: eval
ecosystems: [claude-code, claude-sdk, claude-api]
problem: Many hallucinations can be caught mechanically before running LLM judges without expensive inference
maturity: established
confidence: reported
effort_to_adopt: low
works_with: [llm-as-judge-multi-tier, api-hallucination-prevention]
supersedes: []
sources:
  - {url: "https://zylos.ai/research/2026-04-10-llm-as-judge-production-agent-verification-2026/", kind: blog, date: "2026-04-10"}
  - {url: "https://www.developersdigest.tech/blog/tool-use-claude-api-production-patterns", kind: blog, date: "2026-02-15"}
added: "2026-07-28"
updated: "2026-07-30"
---

## Problem

Expensive LLM judges shouldn't be your first line of defense. A substantial share of agent hallucinations are format errors, schema violations, or missing required fields—things a simple validator catches in milliseconds at zero cost.

## How it works

Deterministic checks run before any LLM judge. They verify:
- **Format:** Is the output valid JSON? Valid Python? Valid syntax?
- **Schema:** Do tool calls have required fields? Are enum values in the allowed set?
- **Bounds:** Is the response within length/token limits? Are numbers in valid ranges?
- **Dependencies:** Do all referenced tools/functions/classes exist in the target environment?
- **Safety:** Does the output match basic safety filters?

These checks fail fast and cheap, reserving LLM judges for semantic questions.

## Setup

1. **Build a validator suite (reusable across your agents):**
```python
class OutputValidator:
    def validate(self, output, schema):
        checks = [
            self.check_format(output),
            self.check_required_fields(output, schema),
            self.check_enum_values(output, schema),
            self.check_bounds(output),
            self.check_safety(output),
        ]
        return all(checks)
    
    def check_format(self, output):
        """JSON, Python, or other syntax."""
        try:
            json.loads(output)
            return True, None
        except:
            return False, "Invalid JSON"
    
    def check_required_fields(self, output, schema):
        """All required fields present."""
        for field in schema.get("required", []):
            if field not in output:
                return False, f"Missing required field: {field}"
        return True, None
    
    def check_enum_values(self, output, schema):
        """Enum fields are in allowed set."""
        for field, field_spec in schema.get("properties", {}).items():
            if "enum" in field_spec and field in output:
                if output[field] not in field_spec["enum"]:
                    return False, f"Invalid enum value for {field}"
        return True, None
    
    def check_bounds(self, output):
        """Strings within length limits, numbers in range."""
        if isinstance(output, str) and len(output) > 100000:
            return False, "Output exceeds length limit"
        # ... additional numeric/range checks
        return True, None
    
    def check_safety(self, output):
        """No explicit safety violations."""
        dangerous = ["rm -rf", "DROP TABLE", "exec(", "eval("]
        for pattern in dangerous:
            if pattern in output:
                return False, f"Dangerous pattern detected: {pattern}"
        return True, None
```

2. **Wire into agent output pipeline:**
```python
def process_agent_output(output, expected_schema):
    # Tier 1: Deterministic checks
    valid, error = validator.validate(output, expected_schema)
    if not valid:
        return {"verdict": "REJECT", "reason": error, "cost": 0}
    
    # Tier 2: Small judge (only if deterministic passes)
    small_judge_result = judge_7b(output, rubric="hallucinated_api,logic")
    if small_judge_result.confidence > 0.75:
        return {"verdict": small_judge_result.verdict, "cost": 0.01}
    
    # Tier 3: Full judge (only if uncertain)
    full_judge_result = judge_claude(output, spec)
    return {"verdict": full_judge_result.verdict, "cost": 0.04}
```

3. **Tool-call validation (especially important):**
```python
def validate_tool_call(call, available_tools):
    """Verify tool exists and has valid arguments."""
    if call.get("name") not in available_tools:
        raise ValueError(f"Unknown tool: {call['name']}")
    
    schema = available_tools[call["name"]]["schema"]
    
    # Check required args
    for req_arg in schema.get("required", []):
        if req_arg not in call.get("arguments", {}):
            raise ValueError(f"Missing required arg: {req_arg}")
    
    # Check arg types
    for arg, value in call.get("arguments", {}).items():
        expected_type = schema["properties"].get(arg, {}).get("type")
        if expected_type and not isinstance(value, expected_type):
            raise ValueError(f"Type mismatch for {arg}")
    
    return True
```

## When to use / when NOT

**Use when:**
- Running agent output through any evaluation pipeline
- Tool use or structured output is involved
- Cost of LLM judges is significant
- Deterministic rejection is safer than silent failure

**NOT when:**
- Semantic correctness is primary concern (need LLM judge anyway)
- Output format is free-form and unpredictable
- Speed is critical and validator overhead matters

## Tradeoffs

**Pros:**
- Catches a substantial share of issues at zero cost
- Fails fast; no wasted LLM calls on obviously invalid outputs
- Easy to debug (clear rejection reasons)
- Reusable across different agents and tasks

**Cons:**
- Misses semantic errors (hallucinated logic, wrong approach)
- Schema must be maintained alongside code
- False positives rare but possible (over-strict validation blocks valid output)

## Example

**Tool call from agent:**
```json
{
  "name": "database.find_users",
  "arguments": {
    "role": "admin"
  }
}
```

**Deterministic checks:**
- Tool exists in available_tools? ✓
- Required arguments present? ✓ (role is required)
- Argument types match schema? ✓ (string)
- Passes safety checks? ✓

**Result:** PASS deterministic, skip expensive judges.

**Contrast:**
```json
{
  "name": "database.get_all_admins",
  "arguments": {}
}
```

**Deterministic checks:**
- Tool exists? ✗ (hallucinated; only `find_users` exists)

**Result:** REJECT immediately. No LLM judge needed.

## Notes & links

- Start with format, required fields, and enum validation—these catch a significant portion of hallucinations mechanistically.
- Tool-call validation is critical: unknown tool names and missing required args are the #1 cause of agent failures in production.
- Combine with [[api-hallucination-prevention]] for defense in depth.
- Schema maintenance: keep tool schemas in a central YAML or JSON file that both the validator and agent documentation use.
