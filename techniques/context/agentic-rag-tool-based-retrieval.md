---
id: agentic-rag-tool-based-retrieval
title: Agentic RAG with tool-based on-demand retrieval over vector search
category: context
ecosystems: [claude-code, claude-sdk, generic]
problem: Pre-computed vector embeddings don't scale to evolving codebases; large corpus RAG adds retrieval latency; traditional RAG can ground answers in incorrect documents
maturity: emerging
confidence: reported
effort_to_adopt: medium
works_with: [prompt-caching-with-claude-api]
supersedes: []
sources:
  - {url: "https://www.techment.com/blogs/rag-in-2026/", kind: blog, date: "2026-07-28"}
  - {url: "https://arxiv.org/html/2501.09136v4", kind: paper, date: "2026-07-28"}
  - {url: "https://buzzgrewal.medium.com/ai-agents-dont-need-vector-search-anymore-inside-the-agentic-search-stack-replacing-rag-in-2026-58efcabe4f6f", kind: blog, date: "2026-07-28"}
added: "2026-07-28"
updated: "2026-07-28"
---

## Problem

Traditional RAG systems pre-index documents into vectors and retrieve by semantic similarity. They can fail silently by grounding confident, well-structured answers in wrong documents. For codebases, embedding-based retrieval misses context-dependent patterns, file relationships, and recent changes. Building and maintaining vector indexes adds complexity and doesn't scale when code evolves rapidly.

## How it works

Agentic RAG replaces pre-computed embeddings with on-demand tool-based retrieval. Agents use lightweight tools (grep, file navigation, semantic search APIs) to pull context just-in-time, dynamically adapting retrieval based on what they've learned.

The pattern mirrors how humans explore a codebase: read a file, follow an import, check a related module, refine hypothesis. Agents perform this same sequential exploration but programmatically.

**Key insight:** Rather than "retrieve all relevant documents upfront," agents maintain lists of references (file paths, search queries, web links) and load data on-demand. This keeps active context focused and lets retrieval adapt mid-task.

## Setup

**1. Expose retrieval as tools/APIs:**

```python
class CodebaseRetrieval:
    async def grep_search(self, pattern: str, path: str = ".") -> List[str]:
        """Search files for pattern; return matching lines with context."""
        
    async def read_file(self, path: str) -> str:
        """Read a single file."""
        
    async def list_files(self, path: str, pattern: str = "*") -> List[str]:
        """List files matching glob pattern."""
        
    async def find_definition(self, symbol: str) -> Optional[Location]:
        """Find where a function/class is defined."""
        
    async def find_references(self, symbol: str) -> List[Location]:
        """Find all calls/usages of a symbol."""
```

**2. Agent uses tools to navigate:**

```javascript
// Agent explores, not pre-loaded docs
const imports = await grep_search("import.*User", "src/");
const userModule = imports[0].file;
const userDef = await read_file(userModule);

// Refine based on findings
if (userDef.includes("validateEmail")) {
    const validation = await find_definition("validateEmail");
    const validationCode = await read_file(validation.file);
}
// Build context incrementally as needed
```

**3. Optional: lightweight indexing for discovery:**

```python
# Fast index for common queries (not full vector embeddings)
index = {
    "functions": [{"name": "getUser", "file": "src/api/user.ts"}, ...],
    "classes": [{"name": "User", "file": "src/models/user.ts"}, ...],
    "tests": [{"pattern": "**/user.test.ts", "count": 5}, ...]
}

# Agent queries index to get starting points
user_files = index["functions"] + index["classes"]  # All User-related
```

## When to use / when NOT

**Use agentic retrieval when:**
- Codebase changes frequently (embeddings get stale)
- Corpus is large (>1M tokens) and most queries need a small slice
- Agent needs to adapt based on findings (iterative exploration)
- Context window is large enough for sequential retrieval (~200K+)
- Explainability/auditability matters (agents show their search steps)

**Use traditional vector RAG when:**
- Corpus is static or changes rarely (embedding cost amortized)
- Document relevance is semantic, not structural (legal docs, knowledge bases)
- Speed is critical (one semantic search vs. multi-step navigation)
- Context window is small (<100K)
- Users need "top-5 documents" without agent reasoning

**NOT suitable for:**
- Real-time latency-critical paths (multi-step retrieval adds latency)
- Unstructured corpora where structure can't be exploited
- Queries needing cross-corpus synthesis (multiple vector indexes)

## Tradeoffs

**Strengths:**
- Retrieval adapts dynamically—agents refine queries based on findings
- Handles evolving codebases—no stale embeddings
- Explainable—agents show their search steps and reasoning
- Leverages structure—symlinks, imports, naming patterns
- Scales with codebase (no re-indexing burden)

**Weaknesses:**
- Higher latency per query (multiple tool calls vs. one vector search)
- Requires well-structured data (filepaths, symbols, clear organization)
- Agents can get lost in large codebases (poor exploration strategy)
- No semantic understanding—grep finds text, not intent

## Example

**Traditional RAG approach:**
```
Vector index of all files (50MB, stale after day)
User asks: "How do we validate emails?"
Retrieve top-5 semantically similar docs
→ May miss recent validation logic
→ Requires periodic re-indexing
```

**Agentic approach:**
```
Agent asked: "How do we validate emails?"
1. Search: grep "validateEmail" . → finds src/utils/email.ts
2. Read: src/utils/email.ts → sees it imports from validator lib
3. Search: find_references("validateEmail") → finds tests and usage
4. Read: test file → understands expected behavior
5. Return: "Found validation logic; here's how it works..."

Context built incrementally; retrieval adapts mid-task
```

**Codebase retrieval agent (pseudocode):**

```python
class CodeAgent:
    async def answer_question(self, question):
        # Start with grep to find entry points
        initial_files = await self.retrieval.grep_search(
            extract_keywords(question)
        )
        
        # Load first file
        context = await self.retrieval.read_file(initial_files[0])
        
        # Loop: refine based on findings
        while not self.satisfied(context):
            # Ask Claude what to explore next
            next_step = await self.model.decide_next_step(context, question)
            
            if next_step.action == "read":
                new_context = await self.retrieval.read_file(next_step.path)
            elif next_step.action == "search":
                results = await self.retrieval.grep_search(next_step.pattern)
                new_context = results[:3]  # Load top 3
            elif next_step.action == "find_def":
                location = await self.retrieval.find_definition(next_step.symbol)
                new_context = await self.retrieval.read_file(location.file)
            
            context += new_context
        
        return await self.model.synthesize(context, question)
```

## Notes & links

- **Hybrid approach:** For codebases under 1M tokens, consider loading the entire repo into context with caching, avoiding retrieval altogether. Use agentic RAG when corpus > 1M or changes frequently.
- **Semantic search tool:** Include one semantic/ML-based search tool for queries where structure fails. Balance syntactic (grep, symbols) and semantic tools.
- **Agent exploration strategy:** Agents benefit from a "search strategy" instruction: prioritize entry points (main, tests), then follow imports, then broaden search. Bad exploration burns tokens.
- **Context compaction:** Combine with context compaction to keep long explorations in-window.
- **Examples:** Claude Code, Cursor, Windsurf, Cline all use tool-based retrieval over vector search for codebases.

See also: [[prompt-caching-with-claude-api]], [[context-compaction-beta]], [[mcp-code-api-over-tools]]
