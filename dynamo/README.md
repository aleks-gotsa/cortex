# Cortex-D: Dynamo Disaggregated Inference

Cortex-D extends the Cortex research engine with NVIDIA Dynamo-style disaggregated inference. Instead of sending all LLM calls to a single endpoint, pipeline stages are routed to specialized worker tiers — prefill workers handle compute-heavy prompt processing with short outputs, while decode workers handle long token generation.

## Architecture

| Worker Type | Pipeline Stages | Characteristics |
|------------|----------------|-----------------|
| **Prefill** | planning, gap_detection | Large input, short JSON output |
| **Decode** | synthesis, verification | Moderate input, long document output |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DYNAMO_ENABLED` | `false` | Enable Dynamo routing (mock or real) |
| `DYNAMO_PREFILL_URL` | `http://localhost:8001/v1` | Prefill worker endpoint |
| `DYNAMO_DECODE_URL` | `http://localhost:8002/v1` | Decode worker endpoint |
| `DYNAMO_TRITON_URL` | `http://localhost:8003` | Triton Inference Server URL |
| `DYNAMO_PREFILL_MODEL` | `meta-llama/Llama-3.1-8B-Instruct` | Model for prefill workers |
| `DYNAMO_DECODE_MODEL` | `meta-llama/Llama-3.1-70B-Instruct` | Model for decode workers |

## Running in Mock Mode

Mock mode routes through Dynamo's architecture but delegates actual inference to Anthropic. Useful for testing routing logic and measuring overhead.

```bash
DYNAMO_ENABLED=true uvicorn backend.main:app --reload --port 8000
```

Log output will show `[MockDynamo]` routing messages indicating which worker type each call is directed to.

## Running in Real Dynamo Mode

See Phase 2 setup — requires GPU hardware with NVIDIA Dynamo workers running on the prefill/decode endpoints.

## Worker Type Mapping

```
planning       → prefill worker (Llama-3.1-8B-Instruct)
gap_detection  → prefill worker (Llama-3.1-8B-Instruct)
synthesis      → decode worker  (Llama-3.1-70B-Instruct)
verification   → decode worker  (Llama-3.1-70B-Instruct)
```
