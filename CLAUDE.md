# CLAUDE.md — Cortex

<project>
<name>Cortex</name>
<type>Open-source deep research engine</type>
<summary>
Search → find gaps → search again → verify every claim → remember everything for next time.
Cheaper than Perplexity. Deeper than Feynman. Gets smarter with each use.
</summary>
</project>

<core_loop>
Query → Planner (Haiku) → Gatherer Pass 1 (Serper + Tavily + crawl4ai + Qdrant) → Reranker (local cross-encoder) → Gap Detector (Sonnet) → Gatherer Pass 2..N (targeted) → Synthesizer (Sonnet) → Verifier (Sonnet) → Memory Writer (Qdrant) → Final Document

Max 3 gathering passes. Stop early if no gaps found.
</core_loop>

<stack>
<backend>FastAPI, Python 3.12, async everywhere</backend>
<search>Serper.dev API + Tavily Search API (both, for redundancy and different result sets)</search>
<scraping>crawl4ai (async, JS rendering capable)</scraping>
<reranking>cross-encoder/ms-marco-MiniLM-L-6-v2 (local, sentence-transformers)</reranking>
<vector_db>Qdrant (Docker, binary quantization, cosine similarity)</vector_db>
<embeddings>BAAI/bge-small-en-v1.5 (local)</embeddings>
<llm provider="anthropic" sdk="anthropic Python SDK">
  <model role="cheap">claude-haiku-4-5-20251001 — planning, sub-question decomposition</model>
  <model role="mid">claude-sonnet-4-20250514 — synthesis, verification, gap detection</model>
  <model role="expensive">claude-opus-4-20250514 — NOT used by default, future adversarial review</model>
</llm>
<frontend>Next.js 14, App Router, TypeScript, Tailwind CSS</frontend>
<storage>SQLite via aiosqlite (research history, run metadata)</storage>
<streaming>Server-Sent Events (SSE) for real-time progress</streaming>
</stack>

<file_structure>
cortex/
├── backend/
│   ├── main.py                 # FastAPI app, CORS, SSE endpoint
│   ├── config.py               # Settings from .env (API keys, URLs)
│   ├── models.py               # Pydantic schemas for everything
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Runs the full pipeline, emits SSE events
│   │   ├── planner.py          # Query → sub-questions + strategy
│   │   ├── gatherer.py         # Runs search + scrape + rerank for one pass
│   │   ├── gap_detector.py     # Evaluates coverage, generates follow-up queries
│   │   ├── synthesizer.py      # All sources → structured document with citations
│   │   ├── verifier.py         # Checks each claim against its cited source
│   │   └── memory.py           # Qdrant read/write
│   ├── search/
│   │   ├── __init__.py
│   │   ├── serper.py           # Serper.dev async client
│   │   ├── tavily.py           # Tavily Search async client
│   │   └── scraper.py          # crawl4ai wrapper
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── router.py           # Picks model based on task type
│   │   └── client.py           # Thin wrapper around anthropic SDK
│   └── storage/
│       ├── __init__.py
│       └── db.py               # SQLite: research runs, history
├── frontend/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx            # Main page: input + results
│   │   └── api/                # Proxy to backend if needed
│   └── components/
│       ├── ResearchInput.tsx    # Query field + depth selector
│       ├── ProgressStream.tsx   # Real-time SSE progress display
│       ├── DocumentView.tsx     # Rendered markdown with citations
│       └── HistoryList.tsx      # Past researches sidebar
├── docker-compose.yml          # Qdrant service
├── requirements.txt
├── .env.example
└── README.md
</file_structure>

<api_design>
<endpoint method="POST" path="/research" response="SSE stream">
<request>
{
  "query": "string",
  "depth": "quick | standard | deep",
  "use_memory": true
}
</request>
<response_events>
event: planning
data: {"sub_questions": ["q1", "q2", "q3"], "strategy": "..."}

event: gathering
data: {"pass": 1, "sources_found": 14, "queries_used": ["...", "..."]}

event: reranking
data: {"top_sources": 8, "dropped": 6}

event: gap_detection
data: {"coverage": {"q1": 0.9, "q2": 0.3, "q3": 0.7}, "gaps": ["q2 needs more data on..."]}

event: gathering
data: {"pass": 2, "sources_found": 5, "targeted_for": ["q2"]}

event: synthesizing
data: {"sections_complete": 2, "total_sections": 4}

event: verifying
data: {"claims_total": 18, "confirmed": 15, "weakened": 2, "removed": 1}

event: memory
data: {"chunks_stored": 12, "collection": "cortex_research"}

event: complete
data: {"document": "# Full markdown...", "sources": [...], "cost_usd": 0.08, "research_id": "abc123"}
</response_events>
</endpoint>

<endpoint method="GET" path="/research/{id}" response="JSON">
Returns full research result from SQLite.
</endpoint>

<endpoint method="GET" path="/research/history" response="JSON">
Returns list of past research runs (id, query, date, cost).
</endpoint>
</api_design>

<pipeline_specs>

<component name="Planner" file="pipeline/planner.py" model="Haiku">
<function>async plan(query: str, prior_context: list[str] | None = None) → ResearchPlan</function>
<system_prompt>
You are a research planner. Your job is to decompose a research query into independent sub-questions.

Rules:
- Generate 3-6 sub-questions that together fully answer the original query
- Each sub-question must be independently searchable
- For each sub-question, provide 2-3 specific search terms
- If prior research context is provided, account for what is already known and focus on gaps

Respond ONLY with valid JSON, no markdown fences, no preamble:
{
  "sub_questions": [
    {"id": "q1", "question": "...", "search_terms": ["term1", "term2"]}
  ],
  "strategy_notes": "brief note on research approach"
}
</system_prompt>
<input>User query + optional prior_context from Qdrant</input>
<output>ResearchPlan with sub_questions list</output>
</component>

<component name="Gatherer" file="pipeline/gatherer.py" model="none (search + local reranker)">
<function>async gather(sub_questions: list[SubQuestion], pass_number: int = 1) → list[Source]</function>
<logic>
1. For each sub-question's search terms:
   a. Run Serper.dev search (async) — top 10 results
   b. Run Tavily Search (async) — top 10 results
   c. Run both in parallel with asyncio.gather
2. Merge all results, deduplicate by URL
3. Take top 8 per sub-question by initial relevance
4. Scrape full content with crawl4ai (async, parallel, max 5 concurrent, 10s timeout per page)
5. Rerank with cross-encoder against the sub-question text
6. Keep top 5 per sub-question
7. Return list of Source objects with full_content populated
</logic>
<source_model>
class Source(BaseModel):
    url: str
    title: str
    snippet: str
    full_content: str | None
    relevance_score: float       # from cross-encoder, 0.0-1.0
    sub_question_id: str
    search_engine: str           # "serper" | "tavily" | "qdrant"
</source_model>
</component>

<component name="Gap Detector" file="pipeline/gap_detector.py" model="Sonnet">
<function>async detect_gaps(sub_questions: list[SubQuestion], sources: list[Source]) → GapReport</function>
<system_prompt>
You evaluate research coverage. For each sub-question, assess how well the gathered sources answer it.

Rules:
- Score each sub-question from 0.0 (no coverage) to 1.0 (fully answered)
- For any score below 0.6, generate 2-3 NEW targeted search queries that would fill the specific gap
- New queries must be meaningfully different from the original search terms — use different angles, terminology, or specificity
- Do not repeat queries that already produced the current sources

Respond ONLY with valid JSON, no markdown fences, no preamble:
{
  "coverage": [
    {"sub_question_id": "q1", "score": 0.9, "assessment": "well covered by sources 1,3,5"},
    {"sub_question_id": "q2", "score": 0.3, "assessment": "only surface-level info found", "follow_up_queries": ["specific query 1", "specific query 2"]}
  ],
  "overall_coverage": 0.65,
  "recommendation": "proceed" | "gather_more"
}
</system_prompt>
<input>Sub-questions + source summaries (title, snippet, first 500 chars of content per source)</input>
<output>GapReport with coverage scores and follow-up queries</output>
<trigger_next_pass>If any sub-question scores below 0.6 AND pass_number &lt; max_passes</trigger_next_pass>
</component>

<component name="Synthesizer" file="pipeline/synthesizer.py" model="Sonnet">
<function>async synthesize(query: str, sub_questions: list[SubQuestion], sources: list[Source]) → str</function>
<system_prompt>
You are a research synthesizer. Write a comprehensive research document from the provided sources.

Rules:
- Every factual claim MUST have an inline citation [1], [2], etc.
- Separate facts from inferences — label inferences with "This suggests..." or "This implies..."
- Never state something as fact if it is your inference
- Structure:
  1. Executive Summary (2-3 paragraphs, key findings only)
  2. Sections organized by theme (NOT by source)
  3. Open Questions (what remains unanswered or contradictory)
  4. Sources (numbered list, every number must match at least one inline citation)
- No unsupported claims. If uncertain, say "Evidence is limited" or "Sources disagree"
- No orphan citations (every [N] in text must appear in Sources)
- No orphan sources (every source must be cited at least once)
- If sources contradict each other, present both sides with their citations

Respond with the full markdown document. No JSON wrapping.
</system_prompt>
<input>Original query + all sources with content (truncate low-relevance sources if approaching context limit — prioritize by relevance_score)</input>
<output>Markdown string with inline citations and sources list</output>
</component>

<component name="Verifier" file="pipeline/verifier.py" model="Sonnet">
<function>async verify(document: str, sources: list[Source]) → VerificationResult</function>
<system_prompt>
You are a research verifier. Your job is to check every cited claim in the document against its source.

For each claim with a citation [N]:
1. Find source [N] in the provided sources
2. Read the source content
3. Determine: does the source ACTUALLY support the SPECIFIC claim made?
4. Verdict: confirmed | weakened | unsupported

Rules:
- "Confirmed" = source directly states or clearly implies the claim
- "Weakened" = source partially supports but the claim overstates or misrepresents
- "Unsupported" = source does not support the claim, or says something different
- For "weakened": rewrite the claim to accurately reflect what the source says
- For "unsupported": remove the claim entirely
- NEVER add new claims. Only verify and correct existing ones.
- NEVER invent sources. Only use what is provided.
- Check for dead reasoning: claims that cite a source about Topic A but make a claim about Topic B

Respond ONLY with valid JSON, no markdown fences, no preamble:
{
  "verified_document": "full corrected markdown document",
  "summary": {
    "confirmed": 15,
    "weakened": 2,
    "removed": 1,
    "details": [
      {"claim": "...", "source_id": 3, "verdict": "weakened", "reason": "source says X not Y", "correction": "revised claim text"}
    ]
  }
}
</system_prompt>
<input>Synthesized document + all sources with full content</input>
<output>VerificationResult with corrected document and verification summary</output>
</component>

<component name="Memory" file="pipeline/memory.py" model="none (embeddings only)">
<function>async store_research(research_id: str, query: str, document: str) → int (chunks stored)</function>
<function>async recall(query: str, top_k: int = 5) → list[str] (relevant chunks from prior research)</function>
<logic>
Store:
1. Chunk final document into ~500 token chunks (split on paragraph boundaries)
2. Embed each chunk with BAAI/bge-small-en-v1.5
3. Store in Qdrant collection "cortex_research" with metadata: {research_id, query, date, chunk_index}

Recall:
1. Embed the new query
2. Search Qdrant for top_k most similar chunks
3. Return chunk texts as prior context

Collection config: cosine similarity, binary quantization.
Create collection on first use if it doesn't exist.
</logic>
</component>

<component name="Orchestrator" file="pipeline/orchestrator.py" model="none (coordination)">
<function>async run_research(request: ResearchRequest) → AsyncGenerator[ResearchEvent]</function>
<logic>
1. RECALL: query Qdrant for prior research (if use_memory=True)
2. PLAN: call planner with query + prior context → yield planning event
3. GATHER PASS 1: call gatherer → yield gathering event
4. GAP DETECT: call gap_detector → yield gap_detection event
5. IF gaps found AND pass &lt; max_passes:
   a. GATHER PASS N: call gatherer with follow-up queries → yield gathering event
   b. GAP DETECT again → yield gap_detection event
   c. Repeat until no gaps or max passes reached
6. SYNTHESIZE: call synthesizer with all accumulated sources → yield synthesizing event
7. VERIFY: call verifier → yield verifying event
8. STORE: save to Qdrant memory → yield memory event
9. SAVE: persist to SQLite → yield complete event with final document

Max passes by depth:
- quick: 1 pass (no gap detection)
- standard: 2 passes max
- deep: 3 passes max
</logic>
</component>

</pipeline_specs>

<search_clients>
<serper file="search/serper.py">
async function search(query: str, num_results: int = 10) → list[SearchResult]
POST https://google.serper.dev/search
Headers: X-API-KEY from config
Body: {"q": query, "num": num_results}
Parse: organic results → SearchResult(url, title, snippet, search_engine="serper")
</serper>

<tavily file="search/tavily.py">
async function search(query: str, num_results: int = 10) → list[SearchResult]
POST https://api.tavily.com/search
Body: {api_key, query, max_results, search_depth: "basic"}
Parse: results → SearchResult(url, title, snippet, search_engine="tavily")
</tavily>
</search_clients>

<scraper file="search/scraper.py">
async function scrape(url: str, timeout: int = 10) → str | None
- Uses crawl4ai AsyncWebCrawler
- Extract markdown content from page
- Skip PDFs and files > 1MB
- Truncate output to 4000 chars
- Return None on any error (never crash the pipeline)

async function scrape_many(urls: list[str], max_concurrent: int = 5) → dict[str, str | None]
- Semaphore-limited parallel scraping
- Returns {url: content} dict
</scraper>

<llm_client file="llm/client.py">
async function call(system: str, user_message: str, model: str, max_tokens: int = 4096) → dict
- Uses anthropic.AsyncAnthropic
- Returns parsed JSON from response
- If JSON parse fails: retry once with appended "Respond ONLY with valid JSON."
- Logs: model, input_tokens, output_tokens per call
- Raises on second failure

Token tracking:
- Accumulate input_tokens and output_tokens across calls
- Expose get_usage() → {input_tokens: int, output_tokens: int, calls: int}
- Expose reset_usage() for per-run tracking
</llm_client>

<llm_router file="llm/router.py">
TASK_MODEL = {
    "planning": "claude-haiku-4-5-20251001",
    "gap_detection": "claude-sonnet-4-20250514",
    "synthesis": "claude-sonnet-4-20250514",
    "verification": "claude-sonnet-4-20250514",
}

PRICING_PER_MILLION = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
}

function get_model(task_type: str) → str
function calculate_cost(model: str, input_tokens: int, output_tokens: int) → float
</llm_router>

<database file="storage/db.py">
<tables>
CREATE TABLE research_runs (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    depth TEXT NOT NULL DEFAULT 'standard',
    status TEXT NOT NULL DEFAULT 'running',
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE research_results (
    id TEXT PRIMARY KEY,
    research_id TEXT NOT NULL REFERENCES research_runs(id),
    document_md TEXT,
    sources_json TEXT,
    verification_json TEXT
);

CREATE TABLE research_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_id TEXT NOT NULL REFERENCES research_runs(id),
    stage TEXT NOT NULL,
    data_json TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
</tables>
Uses aiosqlite. All functions are async.
</database>

<frontend_spec>
<tech>Next.js 14, App Router, TypeScript, Tailwind CSS</tech>
<pages>
- app/page.tsx: main page — input at top, progress in middle, document at bottom
- No other pages needed for v1
</pages>
<components>
- ResearchInput.tsx: text input for query, dropdown for depth (quick/standard/deep), "Research" button. On submit: open EventSource to POST /research
- ProgressStream.tsx: displays SSE events as they arrive. Each stage = one row with icon (spinner while active, checkmark when done), stage name, key metric. Stages appear one by one.
- DocumentView.tsx: renders final markdown document. Citations [1] are clickable anchor links to Sources section. Clean typography, readable line height.
- HistoryList.tsx: fetches GET /research/history. Shows list of past queries with date and cost. Click loads the full result.
</components>
<style>Clean, minimal, dark mode by default. No UI component library. Tailwind utility classes only. Monospace for code, sans-serif for everything else.</style>
</frontend_spec>

<docker_compose>
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
volumes:
  qdrant_data:
</docker_compose>

<env_example>
ANTHROPIC_API_KEY=
SERPER_API_KEY=
TAVILY_API_KEY=
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=cortex_research
DATABASE_PATH=./data/cortex.db
</env_example>

<build_order>
Build and test each piece in this EXACT order. Do not skip ahead. Each step must pass its test before moving to the next.

1. config.py + models.py + main.py (empty SSE endpoint skeleton)
2. llm/client.py + llm/router.py → test: Haiku responds with JSON
3. search/serper.py + search/tavily.py → test: both return search results
4. search/scraper.py → test: scrapes 3 URLs successfully
5. pipeline/planner.py → test: query → sub-questions JSON
6. pipeline/gatherer.py → test: sub-questions → ranked sources with content
7. pipeline/gap_detector.py → test: identifies gaps when sources are incomplete
8. pipeline/synthesizer.py → test: produces cited markdown document
9. pipeline/verifier.py → test: verifies claims, outputs corrected document
10. pipeline/orchestrator.py + main.py SSE wiring → test: curl → full SSE stream → document
11. storage/db.py + GET endpoints → test: history persists and is retrievable
12. pipeline/memory.py + Qdrant → test: research B sees context from research A
13. Cost tracking in client + router → test: cost_usd appears in complete event
14. Frontend: layout + ResearchInput → test: UI sends request to backend
15. Frontend: ProgressStream → test: stages appear in real-time
16. Frontend: DocumentView + HistoryList → test: document renders, history works
17. README.md + .gitignore + final cleanup
</build_order>

<quality_rules>
- Every function has type hints
- Every API response has a Pydantic model
- Every external call (search, scrape, LLM) has try/except with timeout
- Every LLM call logs model name and tokens used
- No print() — use Python logging module
- No hardcoded API keys — everything from .env via config.py
- No global mutable state — pass dependencies explicitly
- Async everywhere in backend — no sync blocking calls
- Backend runs with: uvicorn backend.main:app --reload --port 8000
- Frontend runs with: cd frontend && npm run dev
</quality_rules>

<do_not_build>
- Auth / user accounts / login
- Payment / billing / subscriptions
- Admin dashboard
- Rate limiting beyond basic
- Deployment configs (no Docker for the app, only Qdrant)
- Unit tests (ship first, test later)
- Academic paper search (no AlphaXiv, no arxiv — web search only for v1)
- WebSocket (use SSE, simpler)
- Background job queue (pipeline runs synchronously per request)
</do_not_build>
