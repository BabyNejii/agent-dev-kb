---
id: debate-pattern
title: Debate pattern for multi-perspective verification
category: orchestration
ecosystems: [claude-code, claude-sdk, generic]
problem: Single agent review misses classes of issues (security, performance, tests); need independent perspectives on same code.
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [subagent-fan-out]
supersedes: []
sources:
  - {url: "https://www.tembo.io/blog/claude-code-multi-agent-orchestration", kind: blog, date: 2026-07-28}
  - {url: "https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work", kind: blog, date: 2026-07-28}
  - {url: "https://www.augmentcode.com/guides/swarm-vs-supervisor", kind: blog, date: 2026-07-28}
added: 2026-07-28
updated: 2026-07-28
---

## Problem

A single code reviewer finds one class of issues and stops (bugs, or style, or performance—not all three). Different reviewers have different blind spots. You need multiple independent evaluations to catch issues a single agent would miss.

## How it works

Launch N independent agents to review the same code from different angles, then a **judge agent** synthesizes their findings:

1. **Reviewer A** evaluates for bugs and correctness.
2. **Reviewer B** evaluates for security and auth.
3. **Reviewer C** evaluates for performance and scalability.
4. **Judge** reads all three reviews, dedupes findings, assigns severity, and returns consolidated feedback.

Key: Reviewers work **in parallel on the same input** (not sequentially). They don't see each other's reviews until the judge synthesis phase. This prevents one reviewer's opinion from anchoring the others.

## Setup

```python
code_to_review = """
def authenticate_user(username, password):
    user = db.query(f"SELECT * FROM users WHERE username='{username}'")
    if user and user.password == password:
        return {"user_id": user.id, "token": generate_token()}
    return None
"""

# Launch reviewers in parallel
reviews = {}
for role, prompt in [
    ("correctness", "Look for logical bugs and error handling"),
    ("security", "Look for injection, auth, crypto issues"),
    ("performance", "Look for scalability, DB query, memory issues"),
]:
    reviews[role] = Agent(
        description=f"Reviewer: {role}",
        prompt=f"{prompt}\n\nCode:\n{code_to_review}"
    ).run()

# Judge synthesizes
judge = Agent(
    description="Code review judge",
    prompt=f"Synthesize these reviews into a single report:\n{reviews}"
)
final_review = judge.run()
```

## When to use / when NOT

- **USE** when code quality is critical (security-sensitive, high-traffic, core logic).
- **USE** when you can afford 2x-4x token cost for parallel reviewers + judge.
- **USE** to catch issues no single reviewer would find.
- **NOT** for low-stakes code (refactoring, experiments).
- **NOT** when cost is a constraint (debate costs 2-4x single agent).

## Tradeoffs

- **Cost:** Minimum 3-4 agents (2+ reviewers + judge). At least 3x single-agent cost; can be 5x with complex judge synthesis.
- **Latency:** Reviewers run in parallel, then judge runs serially. Total time: max(reviewer latency) + judge latency.
- **Quality:** Catching multiple issue classes (security + perf + correctness) justifies cost for critical code.
- **Redundancy:** Reviewers often flag the same issues independently. Judge must dedupe.

## Example

Reviewing a REST API endpoint:
```python
Spec: POST /api/users - create new user

Code:
@app.post("/api/users")
def create_user(username: str, email: str, password: str):
    user = User(username=username, email=email, password=hash_password(password))
    db.session.add(user)
    db.session.commit()
    return {"user_id": user.id}
```

**Correctness Reviewer:** "Missing validation for username/email format. What if hash_password fails?"

**Security Reviewer:** "No rate limiting on this endpoint (DOS). Password not salted correctly. SQL injection risk if username not escaped."

**Performance Reviewer:** "db.session.commit() in request path will block. No indexing on email column means create is slow. Missing async/await."

**Judge:** "Consolidated: Critical (SQL injection, no auth), High (rate limiting, password salt), Medium (validation, indexing), Low (async)."

All three catch different issues; single reviewer would have caught ~2.

## Notes & links

Pairs naturally with [[subagent-fan-out]] for dimension-based review.

Research shows multi-agent debate improves answer quality on factual questions; application to code review is similar: independent agents find independent issues.

Judge agent should be prompted to avoid anchoring bias (don't show judge which reviewer said what until after synthesis).
