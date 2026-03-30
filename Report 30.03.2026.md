# Cortex Verification Report — 30.03.2026

Full end-to-end verification of the Cortex deep research engine.

## Environment

| Prerequisite | Version | Status |
|-------------|---------|--------|
| Python | 3.14.3 | Pass |
| Node.js | 25.6.1 | Pass |
| npm | 11.9.0 | Pass |
| Docker | 29.2.0 | Pass |
| Qdrant | latest (Docker) | Pass — healthz check passed |

## Component Verification

| Component | Status | Notes |
|-----------|--------|-------|
| Config | Pass | All env vars loaded. Qdrant: localhost:6333, DB: ./data/cortex.db |
| Models | Pass | ResearchRequest, SubQuestion, ResearchPlan, Source all validate |
| LLM Client | Pass | Haiku responds with JSON, token tracking works (20 in / 19 out) |
| Serper Search | Pass | 3 results returned with URLs, engine="serper" |
| Brave Search | **FAIL** | `BRAVE_API_KEY=placeholder` in `.env` — HTTP 422 from Brave API. Need a real API key. |
| Scraper | Pass | crawl4ai 0.8.6 scraped httpbin.org — 3,598 chars in 0.84s |
| Planner | Pass | 5 sub-questions generated with search terms. Strategy notes present. |
| Database | Pass | SQLite init, create_run, get_run, list_runs all work. |
| Qdrant Memory | Pass | Stored 1 chunk, recalled 3 chunks. BGE-small embeddings load correctly. |
| Full Pipeline | Pass | RAG query — 13,784 char document, 25 sources, citations present, $0.29 cost, SQLite persisted |
| API (SSE) | Pass | FastAPI serves SSE stream. All events emitted in order. `/research/history` returns JSON. |
| Frontend Build | Pass | `tsc --noEmit` clean, `next build` compiled + generated static pages (135 kB first load) |
| MCP Server | Pass | All 4 tools registered: research, recall, history, get_research |

## Integration Test Details

- **Query:** "What is retrieval-augmented generation (RAG) and how does it work?"
- **Depth:** quick (1 pass, no gap detection)
- **Pipeline stages:** planning -> gathering -> synthesizing -> synthesis -> verifying -> memory -> complete
- **Document length:** 13,784 chars
- **Sources found:** 25
- **Verification:** 24 claims checked — 20 confirmed, 2 weakened, 2 removed
- **Cost:** $0.2888
- **Persistence:** Run + result stored in SQLite, 4 chunks stored in Qdrant

## API Test Details

- **SSE streaming:** All events emitted in correct order (planning, gathering, synthesizing, synthesis, verifying, complete)
- **History endpoint:** Returns JSON array of past runs with id, query, depth, status, cost, timestamps
- **Second query:** "What is WebAssembly?" — 38 claims checked, 35 confirmed, 2 weakened, 1 removed

## What Needs Fixing

### 1. Brave Search API Key (only failure)

The `.env` file has `BRAVE_API_KEY=placeholder`. The pipeline gracefully degrades (Serper alone produced 25 sources), but the redundancy benefit of dual-engine search is lost. Replace `placeholder` with a real Brave Search API key from https://api.search.brave.com.

## Conclusion

**Cortex is operational.** 13 out of 14 components pass. The only failure is the missing Brave API key — a configuration issue, not a code issue. The pipeline, API, frontend, and MCP server all work end-to-end.
