# Cortex — Claude Code Prompt

Replace Brave Search with Tavily, then deploy the full stack.

## Part 1 — Code changes

1. Delete backend/search/brave.py. Create backend/search/tavily.py — async Tavily client using httpx. POST https://api.tavily.com/search with body {api_key, query, max_results, search_depth: "basic"}. Parse response.results → list[SearchResult] with url, title, snippet, search_engine="tavily".

2. backend/config.py — replace BRAVE_API_KEY with TAVILY_API_KEY.

3. backend/pipeline/gatherer.py — replace brave import and brave.search() call with tavily.search(). Keep the same parallel asyncio.gather pattern with serper.

4. .env.example — replace BRAVE_API_KEY= with TAVILY_API_KEY=

5. README.md — replace "Brave Search API" with "Tavily Search API" in the stack table and anywhere else it appears.

6. CLAUDE.md — in the <search> tag replace "Brave Search API" with "Tavily Search API".

Do not change anything else in the code. Keep all other pipeline logic identical.

## Part 2 — Deploy

BACKEND — deploy to Render:
- Create render.yaml in project root:
  services:
    - type: web
      name: cortex-backend
      runtime: python
      buildCommand: pip install -r requirements.txt && python -m playwright install chromium
      startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
      envVars:
        - key: ANTHROPIC_API_KEY
          sync: false
        - key: SERPER_API_KEY
          sync: false
        - key: TAVILY_API_KEY
          sync: false
        - key: QDRANT_URL
          sync: false
        - key: QDRANT_API_KEY
          sync: false
        - key: QDRANT_COLLECTION
          value: cortex_research
        - key: DATABASE_PATH
          value: ./data/cortex.db

- Push all changes to GitHub
- Tell me the Render backend URL after deployment so I can update the frontend config

FRONTEND — deploy to Vercel:
- In frontend/next.config.mjs add:
  env: { NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL }
- Update all fetch calls in frontend/lib/research.ts to use process.env.NEXT_PUBLIC_API_URL as base URL (fallback to http://localhost:8000)
- Run: cd frontend && vercel --prod
- Set NEXT_PUBLIC_API_URL=<render_backend_url> in Vercel dashboard environment variables

After both are deployed, run a test: POST /research with query "What is RAG?" and depth "quick" against the Render URL and confirm SSE stream returns a complete event.
