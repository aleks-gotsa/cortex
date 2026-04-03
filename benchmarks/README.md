# Cortex Benchmarks

Standalone benchmark harness for measuring Cortex research engine performance.

## Prerequisites

Ensure the Cortex backend is running:

```bash
cd /path/to/cortex
python -m backend.main
```

Set API keys in your environment:

```bash
export ANTHROPIC_API_KEY=...
export SERPER_API_KEY=...
export TAVILY_API_KEY=...
```

## Usage

```bash
# Run 5 mixed-depth queries against localhost
python -m benchmarks.runner

# Run 10 quick queries against a remote backend
python -m benchmarks.runner --url https://api.example.com --n 10 --depth quick

# Run all 20 queries
python -m benchmarks.runner --n 20 --depth mixed
```

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | `http://localhost:8000` | Backend URL |
| `--n` | `5` | Number of queries (max 20) |
| `--depth` | `mixed` | `quick`, `standard`, `deep`, or `mixed` |
| `--output` | `benchmarks/results/` | Output directory |

## Output

Each run produces:

- `raw_{timestamp}_{i}.json` — per-query raw metrics
- `report_{timestamp}.md` — markdown summary table
- `report_{timestamp}.csv` — CSV for further analysis

## Interpreting Results

| Metric | What it means |
|--------|---------------|
| **TTFF** | Time to first SSE event — measures initial responsiveness |
| **Total time** | Full pipeline duration from request to completion |
| **Cost/query** | USD cost reported by the backend (LLM + search API costs) |
| **Throughput** | Queries per minute (sequential, not concurrent) |
| **Success rate** | Percentage of queries that completed without error |

Lower TTFF and total time = better. The p50 is the median, p95/p99 show tail latency.
