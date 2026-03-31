# Cortex

Multi-layer research engine with cumulative memory and cost-efficient model routing.

Search -> find gaps -> search again -> verify every claim -> remember everything for next time.

## What Makes It Different

| Feature | Perplexity | Feynman | Cortex |
|---------|-----------|---------|--------|
| Search depth | Single pass | Single pass | Up to 3 iterative passes |
| Gap detection | No | No | Automatic coverage scoring + targeted follow-up |
| Claim verification | No | No | Every citation checked against its source |
| Memory | No | No | Qdrant vector DB recalls prior research |
| Cost control | Opaque | Opaque | Model routing: Haiku for planning, Sonnet for synthesis |
| Source transparency | Partial | Yes | Full inline citations with verification verdicts |
| Self-hosted | No | No | Yes, fully open-source |

## Architecture

```mermaid
graph TD
    Q[User Query] --> P[Planner<br/>Haiku]
    P --> G1[Gatherer Pass 1<br/>Serper + Tavily + crawl4ai]
    G1 --> R[Reranker<br/>cross-encoder local]
    R --> GD{Gap Detector<br/>Sonnet}
    GD -->|Gaps found| G2[Gatherer Pass 2..N<br/>targeted queries]
    G2 --> R
    GD -->|Coverage OK| S[Synthesizer<br/>Sonnet]
    S --> V[Verifier<br/>Sonnet]
    V --> M[Memory Writer<br/>Qdrant + BGE embeddings]
    M --> D[Final Document<br/>with verified citations]

    QD[(Qdrant<br/>Vector Memory)] -.->|prior context| P
    QD -.-> M
    DB[(SQLite<br/>History)] -.-> D
```

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/aleks-gotsa/cortex.git
cd cortex
cp .env.example .env
```

Edit `.env` with your API keys:

```
ANTHROPIC_API_KEY=sk-ant-...
SERPER_API_KEY=...
TAVILY_API_KEY=...         # optional — Serper alone works fine
```

### 2. Start Qdrant (vector memory)

```bash
docker-compose up -d
```

### 3. Install and run backend

```bash
pip install -r requirements.txt
python -m playwright install chromium   # for crawl4ai scraping
uvicorn backend.main:app --reload --port 8000
```

### 4. Install and run frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Usage

### Via the web UI

1. Enter a research query
2. Select depth: **quick** (1 pass), **standard** (2 passes), or **deep** (3 passes)
3. Watch real-time progress as each pipeline stage completes
4. Read the verified document with inline citations
5. Browse past research in the sidebar

### Via curl

```bash
# Stream a research session
curl -N -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What is retrieval augmented generation?", "depth": "quick"}'

# Get research history
curl http://localhost:8000/research/history

# Get a specific result
curl http://localhost:8000/research/{research_id}
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/research` | Start research, returns SSE stream |
| `GET` | `/research/history` | List past research runs |
| `GET` | `/research/{id}` | Get full result by ID |

### SSE Events

The `/research` endpoint streams these events in order:

| Event | Data |
|-------|------|
| `planning` | sub_questions, strategy |
| `gathering` | pass number, sources_found, queries_used |
| `gap_detection` | coverage scores, gaps (skipped for `quick`) |
| `synthesizing` | — |
| `verifying` | confirmed, weakened, removed counts |
| `memory` | chunks_stored, collection |
| `complete` | document, sources, cost_usd, research_id |

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.12+, async everywhere |
| LLM | Anthropic Claude (Haiku for planning, Sonnet for synthesis/verification) |
| Search | Serper.dev + Tavily Search API |
| Scraping | crawl4ai (Playwright-based, JS rendering) |
| Reranking | cross-encoder/ms-marco-MiniLM-L-6-v2 (local) |
| Embeddings | BAAI/bge-small-en-v1.5 (local) |
| Vector DB | Qdrant (Docker) |
| Storage | SQLite via aiosqlite |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Streaming | Server-Sent Events (SSE) |

## Cost Estimates

| Depth | Passes | Typical Cost | Time |
|-------|--------|-------------|------|
| Quick | 1 | ~$0.08-0.15 | ~30s |
| Standard | 2 | ~$0.15-0.25 | ~60s |
| Deep | 3 | ~$0.25-0.40 | ~90s |

Costs depend on query complexity and source volume. Haiku handles planning at 1/4 the cost of Sonnet.

## Project Structure

```
cortex/
├── backend/
│   ├── main.py              # FastAPI app, SSE endpoint
│   ├── config.py            # Settings from .env
│   ├── models.py            # Pydantic schemas
│   ├── pipeline/
│   │   ├── orchestrator.py  # Full pipeline coordination
│   │   ├── planner.py       # Query decomposition (Haiku)
│   │   ├── gatherer.py      # Search + scrape + rerank
│   │   ├── gap_detector.py  # Coverage evaluation (Sonnet)
│   │   ├── synthesizer.py   # Document generation (Sonnet)
│   │   ├── verifier.py      # Claim verification (Sonnet)
│   │   └── memory.py        # Qdrant read/write
│   ├── search/
│   │   ├── serper.py        # Serper.dev client
│   │   ├── tavily.py        # Tavily Search client
│   │   └── scraper.py       # crawl4ai wrapper
│   ├── llm/
│   │   ├── client.py        # Anthropic SDK wrapper
│   │   └── router.py        # Model selection + cost tracking
│   └── storage/
│       └── db.py            # SQLite persistence
├── frontend/
│   ├── app/                 # Next.js App Router
│   └── components/          # React components
├── docker-compose.yml       # Qdrant service
├── requirements.txt
└── .env.example
```

## MCP Server

Use Cortex as a tool from Claude Desktop, claude.ai, or any MCP client.

### Run

```bash
python mcp_server.py
# or
fastmcp run mcp_server.py
```

### Claude Desktop config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cortex": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/absolute/path/to/cortex"
    }
  }
}
```

### Available tools

| Tool | Description | Params |
|------|-------------|--------|
| `research` | Run full research pipeline (30-90s) | `query` (str), `depth` ("quick"\|"standard"\|"deep"), `use_memory` (bool) |
| `recall` | Search Qdrant memory for prior research | `query` (str), `top_k` (int) |
| `history` | List past research runs | `limit` (int) |
| `get_research` | Retrieve a specific past result | `research_id` (str) |

## License

MIT
