# Research Document: Difference Between Prefill and Decode in LLM Inference

## Executive Summary
This research document explores the differences between prefill and decode phases in large language model (LLM) inference, focusing on their roles, advantages, and potential use cases. The primary function of prefill is to process input tokens and produce an initial key-value (KV) cache, while decode generates output tokens using this cache. Disaggregated serving can be beneficial when prefill and decode require different resource shapes, such as handling long prompts or generating long outputs. However, the choice between prefill and decode depends on specific workload characteristics.

## Prefill in LLM Inference
Prefill is a critical phase in LLM inference that processes input tokens to produce an initial key-value (KV) cache [1], [2]. This cache stores intermediate states necessary for generating subsequent output tokens. The primary function of prefill is to handle the prompt and prepare the model for decoding [3].

### Key Functions
- **Input Token Processing**: Prefill takes in a series of input tokens, which are then contextualized within the scope of the context window.
- **KV Cache Generation**: It generates an initial KV cache that stores intermediate states required for efficient token generation during the decode phase.

### Scaling Pressure
Prefill faces scaling challenges related to:
- **Input Length and Prompt Reuse**: Longer prompts or repeated prompts can increase the computational load [1].
- **Context Size**: Larger context sizes require more memory and processing power, which can limit throughput [2].

## Decode in LLM Inference
Decode is responsible for generating output tokens using the KV cache produced by prefill. This phase involves autoregressive token generation until a stopping criterion is met.

### Key Functions
- **Token Generation**: Decodes generate subsequent tokens based on the context provided by the KV cache.
- **Output Length and Concurrency**: The decode phase can be constrained by output length, active KV memory, and concurrency requirements [1].

## Advantages of Prefill Over Decode
Prefill offers several advantages over decode in certain scenarios:
- **Resource Management**: Disaggregated serving allows independent scaling of prefill and decode workers, optimizing resource utilization for different workloads [1].
- **KV Cache Optimization**: Efficient management of the KV cache can significantly reduce memory wastage, enabling larger batch sizes and throughput [3].

## Can Prefill Replace Decode?
While prefill is crucial for generating an initial KV cache, it cannot replace decode. Decode remains essential for autoregressive token generation, which requires ongoing access to the KV cache.

### Open Questions
- **Workload Characteristics**: What specific workload characteristics make disaggregated serving more beneficial than aggregated deployment?
- **Resource Allocation**: How can resource allocation between prefill and decode be optimized in real-world scenarios?
