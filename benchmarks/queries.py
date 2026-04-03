"""Benchmark test queries for Cortex research engine."""

QUERIES: list[dict[str, str]] = [
    {"query": "What is retrieval-augmented generation?", "depth": "quick"},
    {"query": "How do transformer attention mechanisms work?", "depth": "quick"},
    {"query": "What are the key differences between GPT-4 and Claude?", "depth": "standard"},
    {"query": "How does NVIDIA Dynamo disaggregated inference work?", "depth": "standard"},
    {"query": "What is KV-cache and why does it matter for LLM serving?", "depth": "quick"},
    {"query": "How do vector databases work?", "depth": "quick"},
    {"query": "What is the difference between prefill and decode in LLM inference?", "depth": "standard"},
    {"query": "How does Triton Inference Server work?", "depth": "standard"},
    {"query": "What are the best practices for deploying LLMs in production?", "depth": "standard"},
    {"query": "How does RLHF training work?", "depth": "quick"},
    {"query": "What is speculative decoding in LLMs?", "depth": "standard"},
    {"query": "How does flash attention reduce memory usage?", "depth": "standard"},
    {"query": "What is model quantization and what are the tradeoffs?", "depth": "quick"},
    {"query": "How do mixture of experts models work?", "depth": "standard"},
    {"query": "What is the current state of open source LLMs in 2026?", "depth": "deep"},
    {"query": "How does NVIDIA NIM simplify LLM deployment?", "depth": "standard"},
    {"query": "What are the main bottlenecks in LLM inference throughput?", "depth": "standard"},
    {"query": "How does continuous batching work in LLM serving?", "depth": "standard"},
    {"query": "What is tensor parallelism in distributed LLM inference?", "depth": "deep"},
    {"query": "How does PagedAttention improve KV cache efficiency?", "depth": "deep"},
]
