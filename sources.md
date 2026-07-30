# Ingestion sources (watchlist)

What the pipeline (`INGEST.md`, `/ingest`) sweeps. Ordered by signal-to-noise, highest first.

**Every entry below was existence-checked on 2026-07-30**: arXiv IDs resolved through the arXiv
API, GitHub repos through the GitHub API (with last-push dates), web sources by HTTP status.
Nothing here is unverified. When adding a source, check it the same way — a dead link in a
watchlist fails silently, which is worse than no entry.

**`feed`** means there is something cheap to diff for *new* items (GitHub releases/commits, a
REST endpoint, RSS). Those are the only sources worth automating; the rest need a manual look.

---

## Tier 1 - official / first-party (highest authority)

Only these can promote an entry to `confidence: verified`.

| Source | URL | feed |
|---|---|---|
| Claude Code docs | https://code.claude.com/docs | no |
| Claude docs / API | https://platform.claude.com/docs · https://docs.claude.com | no |
| Claude Code changelog | github.com/anthropics/claude-code `CHANGELOG.md` | yes |
| Claude Agent SDK changelog | github.com/anthropics/claude-agent-sdk-python | yes |
| Anthropic cookbook | github.com/anthropics/claude-cookbooks | yes |
| Anthropic official skills | github.com/anthropics/skills | yes |
| Anthropic engineering blog | https://www.anthropic.com/engineering | no |
| MCP specification | github.com/modelcontextprotocol/modelcontextprotocol | yes |
| MCP registry | github.com/modelcontextprotocol/registry | yes |
| Google Antigravity docs | https://antigravity.google/docs/home | no |

**MCP registry has a REST API supporting `updated_since`** (https://registry.modelcontextprotocol.io) -
the cleanest automation hook found: poll for deltas instead of re-scraping a directory.

## Tier 2 - curated community catalogues

Cap at `confidence: reported`. Useful for *discovering* techniques to then confirm against Tier 1.

| Source | URL | note |
|---|---|---|
| awesome-agentic-patterns | github.com/nibzard/awesome-agentic-patterns | closest project to ours; editorial gatekeeping, each entry explained |
| awesome-harness-engineering | github.com/ai-boost/awesome-harness-engineering | 250+ annotated entries on the harness layer; very active |
| Awesome-Context-Engineering | github.com/Meirtz/Awesome-Context-Engineering | context/memory techniques |
| Agent-Skills-for-Context-Engineering | github.com/muratcankoylan/Agent-Skills-for-Context-Engineering | context-engineering skills, multi-platform |
| awesome-claude-skills | github.com/travisvn/awesome-claude-skills | community Claude Code skills |
| agentics | github.com/githubnext/agentics | GitHub-native agentic workflow patterns |
| agentic-ai-knowledge-base | github.com/ankurkumarz/agentic-ai-knowledge-base | broad lifecycle KB; small but same philosophy |
| Agentic-Design-Patterns | github.com/josephsenior/Agentic-Design-Patterns | runnable pattern implementations |
| agents-md | github.com/Austin1serb/agents-md | AGENTS.md / instruction-file patterns |
| LangGraph | github.com/langchain-ai/langgraph | orchestration patterns worth stealing; `feed` |
| CrewAI | github.com/crewaiinc/crewai | multi-agent orchestration; `feed` |
| OpenAI cookbook | https://cookbook.openai.com | cross-ecosystem recipes |

## Tier 3 - papers, surveys, taxonomies, benchmarks

Cap at `reported`. Best for validating our category scheme and for evaluation methodology.

**Surveys / taxonomies** (all IDs API-verified):
- `2508.01186` A Survey on Agent Workflow - Status and Future
- `2606.31518` Design and Implementation of Agentic Orchestrations
- `2604.03515` Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures
- `2601.12560` Agentic AI: Architectures, Taxonomies, and Evaluation
- `2503.21460` LLM Agent: Survey on Methodology, Applications, Challenges
- `2507.21504` Evaluation and Benchmarking of LLM Agents: A Survey
- `2508.12683` A Taxonomy of Hierarchical Multi-Agent Systems
- `2502.14321` Beyond Self-Talk: Communication-Centric Survey of Multi-Agent LLMs
- `2607.21503` Agentic Context Management: Agent Memory and Cost - directly relevant to token work
- `2602.06052` / `2602.19320` memory-mechanism surveys

**Benchmarks / leaderboards:** `2509.16941` SWE-Bench Pro · `2412.14161` TheAgentCompany ·
`2308.03688` AgentBench · `2508.07575` MCPToolBench++ · https://swe-rebench.com

**Paper collections:** github.com/VoltAgent/awesome-ai-agent-papers ·
github.com/Asaf-Yehudai/LLM-Agent-Evaluation-Survey ·
github.com/Shichun-Liu/Agent-Memory-Paper-List

## Tier 4 - practitioner media (highest noise)

Cap at `confidence: speculative` until corroborated by a Tier 1 or 2 source.

| Source | URL | cadence | rss |
|---|---|---|---|
| Simon Willison | https://simonw.substack.com (+ simonwillison.net) | frequent | yes |
| Latent Space | https://www.latent.space | weekly | yes |
| Made by Agents | https://www.madebyagents.com/newsletter | weekly | yes |
| GitHub Blog (AI/agents) | https://github.blog | irregular | yes |

Plus targeted checks: Hacker News and r/ClaudeAI threads on Claude Code / MCP workflows.

### Demoted on review (kept as a record, do not treat as live)

- **Agentic Coding Newsletter** (agenticinsights.substack.com) - a research agent rated this
  Tier 1, but its last dated post is **2025-09-17**, ~10 months stale. Demoted: check manually
  before trusting, and drop it entirely if nothing new appears.
- **github.com/luo-junyu/awesome-agent-papers** - last push 2025-11-07. Going stale; superseded
  in practice by the paper collections listed in Tier 3.

---

## Filter rules for the pipeline

- Keep only techniques applicable to **building software** with agents. A tool *directory* is
  not a technique catalogue - most MCP/framework listings are discovery aids, not sources.
- Claude-first; tag `antigravity` / `mcp` / `generic` when a technique transfers.
- Tier decides the confidence ceiling: Tier 1 -> may reach `verified`; Tier 2/3 -> `reported`;
  Tier 4 -> `speculative` until corroborated.
- Skip pure product announcements, funding news, and model-release hype with no reusable
  technique. This is most of what AI media publishes.
- Never carry a statistic whose only source is a single low-authority blog. Either corroborate
  it independently or state the claim qualitatively without the number.
- Re-check a source's last-updated date before relying on it. Staleness is the common failure
  mode here, not fabrication.

## Prior art

Nothing found does what this KB does: a Claude-primary technique catalogue where **every entry
carries an explicit confidence grade tied to first-party documentation**. The nearest neighbours
are `awesome-agentic-patterns` (editorially curated patterns, no confidence model) and
`agentic-ai-knowledge-base` (broader lifecycle scope, much smaller). Academic taxonomies cluster
around 3-6 component dimensions (perception/planning/action/memory/collaboration) rather than the
operational split used here - no published taxonomy covers `codebase-ops` or `integration` as
first-class categories.
