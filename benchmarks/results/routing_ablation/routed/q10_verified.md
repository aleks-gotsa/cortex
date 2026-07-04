# Executive Summary

Speculative decoding is an optimization technique for large language models (LLMs) that aims to reduce inference latency by generating multiple tokens in a single forward pass. This method alternates between drafting and verification phases, where a smaller draft model proposes candidate sequences, which are then verified by the larger target model. The primary benefits of speculative decoding include significant reductions in latency without compromising output quality. However, its effectiveness can vary depending on the specific use case and the size difference between the draft and target models.

This document explores speculative decoding through various sources, providing a comprehensive understanding of how it works, its advantages, and comparisons with other decoding methods. Open questions remain regarding the optimal configuration for different model sizes and the broader implications for LLM inference optimization.

# Speculative Decoding

## What is Speculative Decoding?

Speculative decoding is an inference-time optimization technique designed to reduce latency in large language models (LLMs) by generating multiple tokens per decoding step [1][2]. It operates through two phases: drafting and verification. During the drafting phase, a smaller draft model proposes candidate sequences of tokens. The larger target model then verifies these candidates in a single forward pass using a modified rejection sampling scheme.

### How Does Speculative Decoding Work?

The process involves alternating between drafting and verification phases:
1. **Drafting**: A fast approximation model (draft model) generates a short sequence of candidate tokens.
2. **Verification**: The target model scores the entire draft sequence in one batched forward pass, comparing drafts against the target probabilities.
This approach leverages the fact that for large models, computing a single token and several tokens take roughly the same time due to memory bandwidth constraints [1][3].

## Benefits of Speculative Decoding

### Reduced Latency

Speculative decoding can reduce latency by approximately two to three times compared to standard autoregressive decoding. This is achieved through parallel processing during the verification phase, where multiple candidate sequences are evaluated simultaneously.

### No Change in Output Quality

The technique preserves the target model's original output distribution, ensuring that speculative decoding produces identical results as standard decoding [1][2].

## Comparison with Other Decoding Methods

### Versus Greedy Decoding

Greedy decoding is suited for input-grounded tasks and factual knowledge-seeking. Speculative decoding offers significant latency reductions but may require careful tuning of temperature parameters to maintain output quality, especially in open-ended tasks requiring creativity.

### Versus Assisted Generation

Assisted generation involves using a smaller model as an assistant to the larger target model. While speculative decoding can achieve similar benefits, it requires more complex implementation and may not always be applicable depending on the specific use case [5][6].

# Open Questions
1. **Optimal Configuration**: What is the ideal size difference between the draft and target models for different LLMs?
2. **Generalizability**: How well does speculative decoding generalize across various types of tasks and model architectures?
3. **Resource Utilization**: Can speculative decoding be further optimized to reduce memory usage while maintaining performance gains?
