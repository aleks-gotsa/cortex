# Executive Summary

Speculative decoding is an optimization technique for large language models (LLMs) that aims to reduce inference latency by generating multiple tokens in a single forward pass. This method alternates between drafting and verification phases, where a smaller draft model proposes candidate sequences, which are then verified by the larger target model. The primary benefit of speculative decoding is its ability to significantly decrease the time required for token generation without altering the final output distribution.

This technique has been shown to achieve up to 2-3 times faster inference compared to standard autoregressive decoding while maintaining identical outputs. It leverages the observation that memory bandwidth, rather than arithmetic throughput, is often the bottleneck in LLMs during inference. By generating multiple tokens at once, speculative decoding can reduce the number of forward passes required, thereby accelerating the overall process.

However, several questions remain unanswered regarding its optimal implementation and broader applicability across different model architectures and tasks. Additionally, while speculative decoding offers significant speed improvements, it may not be universally applicable to all types of LLMs or tasks.

# Speculative Decoding in Context

## Definition
Speculative decoding is an inference-time optimization for autoregressive large language models (LLMs) that generates multiple tokens per decoding step instead of one. A smaller draft model proposes a sequence of candidate tokens, and the larger target model verifies them in a single forward pass through a modified rejection sampling scheme [1][3].

## Mechanism
The technique alternates between two phases: drafting and verification.
- **Drafting**: A fast approximation model generates a short run of K candidate tokens. The draft model is usually a much smaller version of the target model or a lightweight auxiliary network.
- **Verification**: The target model scores the entire draft sequence in one batched forward pass. A modified rejection sampling algorithm compares the draft and target probabilities at each position to verify the candidates.

## Efficiency Improvement
Speculative decoding improves efficiency by reducing the number of forward passes required for token generation. Since memory bandwidth is often the bottleneck, generating multiple tokens simultaneously can significantly decrease latency [1][3].

# Examples of Speculative Decoding
- **T5-XXL**: The technique has been demonstrated on T5-XXL models, achieving a 2X to 3X acceleration compared to standard decoding with identical outputs [2].
- **General LLMs**: While speculative decoding is particularly effective for large models, its applicability extends to various model architectures and tasks. However, the optimal implementation may vary depending on the specific model and task requirements.

# Open Questions
1. **Optimal Implementation**: What are the best practices for implementing speculative decoding across different model architectures?
2. **Task-Specific Applications**: How does speculative decoding perform in diverse LLM applications beyond T5-XXL models?
3. **Trade-offs**: Are there any trade-offs or limitations associated with using speculative decoding, such as increased memory usage during verification?

# Sources
1. Leviathan, Yaniv; Kalman, Matan; Matias, Yossi (2023). *Fast Inference from Transformers via Speculative Decoding*. Proceedings of the 40th International Conference on Machine Learning (ICML).
2. Chen, Charlie; Borgeaud, Sebastian; Irving, Geoffrey; Lespiau, Jean-Baptiste; Sifre, Laurent; Jumper, John (2023-02-02). *Accelerating Large Language Model Decoding with Speculative Sampling*. arXiv:2302.01318 [cs.CL].
