```markdown
# Executive Summary

This research document explores the differences between prefill and decode in LLM inference, drawing from various sources. The key findings are that during LLM inference, the prefill phase processes the input tokens to produce an initial key-value (KV) cache, while the decode phase generates output tokens using this cache. Disaggregated serving, as described by NVIDIA's user guide [1], separates these phases into independent worker pools for better scalability and resource management. The document also highlights that managing the KV cache efficiently is crucial due to its significant memory footprint.

# Sections

## Prefill vs Decode in LLM Inference
Prefill involves processing the input tokens to produce an initial key-value (KV) cache, while decode generates output tokens using this cache [1][2]. This separation allows for independent scaling of resources and can optimize performance based on specific workload requirements. The prefill phase is more sensitive to input length and prompt reuse, whereas the decode phase is more affected by concurrency and output length.

## Disaggregated Serving
Disaggregated serving separates the prefill and decode phases into distinct worker pools [1]. This approach enables better resource allocation and can be particularly beneficial when one phase becomes a bottleneck. For instance, long prompts or retrieval-heavy traffic make prefill expensive, while long generations or high concurrency make decode the bottleneck.

## Key-Value Cache Management
Efficient management of the KV cache is critical for LLM inference due to its significant memory footprint [3][4]. Techniques such as PagedAttention and optimizations in attention mechanisms can help reduce memory wastage. The size of the KV cache per token is given by a formula that depends on model parameters, batch size, and sequence length.

## Model Parallelization
Model parallelization techniques like pipeline parallelism can be used to distribute the model across multiple GPUs, reducing the per-device memory footprint [5]. This approach enables running larger models or handling larger batches of inputs. However, it is less relevant during inference compared to data parallelism, which is more commonly used for training.

## Transformer Architecture
The transformer architecture, as described in Wikipedia [6][7], involves tokenization and contextualization through a multi-head attention mechanism. This mechanism allows each token to be processed independently within the context window, enabling efficient parallel processing of input sequences.

# Open Questions

- How do different model parallelization techniques (e.g., tensor parallelism) impact LLM inference?
- What are the trade-offs between disaggregated serving and aggregated deployment in terms of performance and resource utilization?

# Sources

1. Disaggregated serving — NVIDIA Dynamo user guide
   URL: https://docs.nvidia.com/dynamo/user-guides/disaggregated-serving
   
2. Mastering LLM Techniques: Inference Optimization — NVIDIA Developer Blog (part 1)
   URL: https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/
   
3. Mastering LLM Techniques: Inference Optimization — NVIDIA Developer Blog (part 2)
   URL: https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/
   
4. Mastering LLM Techniques: Inference Optimization — NVIDIA Developer Blog (part 3)
   URL: https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/
   
5. Mastering LLM Techniques: Inference Optimization — NVIDIA Developer Blog (part 4)
   URL: https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/
   
6. Transformer (deep learning architecture) — Wikipedia
   URL: https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)
```