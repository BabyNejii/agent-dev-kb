# Ingestion sources (watchlist)

The ingestion pipeline (`INGEST.md`) sweeps these. Ordered by signal-to-noise:
highest first. Add/remove freely.

## Tier 1 — official docs & changelogs (highest signal, easiest to verify)

- Anthropic docs — https://docs.anthropic.com
- Claude Code docs — https://docs.claude.com/en/docs/claude-code
- Claude Code release notes / changelog
- Claude Agent SDK docs
- Anthropic engineering blog — https://www.anthropic.com/engineering
- Antigravity (Google) docs & release notes
- Model Context Protocol docs — https://modelcontextprotocol.io

## Tier 2 — GitHub (structured, API-accessible)

- anthropics/* repos (claude-code, agent SDK, cookbook)
- modelcontextprotocol/* (servers, spec)
- "awesome-claude" / "awesome-agents" / "awesome-mcp" lists
- Notable MCP server repos
- Antigravity-related repos and integrations

## Tier 3 — blogs, papers, newsletters (needs relevance filter)

- arXiv cs.SE / cs.AI (agentic software engineering)
- Engineering blogs covering agent dev workflows
- Latent Space, Pragmatic Engineer, and similar

## Tier 4 — social (highest noise — aggressive filter required)

- X/Twitter: agent-building practitioners
- Reddit: r/ClaudeAI, r/LocalLLaMA (dev-workflow posts only)
- Hacker News: agent/Claude/MCP threads
- Relevant Discords (manual, when notable)

## Filter rules for the pipeline

- Keep only techniques applicable to **building software** with agents.
- Claude-first; tag `antigravity`/`mcp`/`generic` when a technique transfers.
- Social/blog items enter as `confidence: speculative` until corroborated.
- Skip pure product announcements with no reusable technique.
