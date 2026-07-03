# Speculative Decoding in Large Language Models (LLMs)

## Executive Summary

Speculative decoding is an optimization technique for large language models (LLMs) that aims to reduce inference latency by generating multiple tokens per decoding step. This method alternates between a _drafting_ phase, where a smaller model proposes candidate token sequences, and a _verification_ phase, where the larger target model evaluates these candidates in one batched forward pass. The technique preserves the original output distribution of the target model while significantly reducing latency by up to 2-3 times compared to standard decoding methods.

## Speculative Decoding Mechanism

### Drafting Phase
During the drafting phase, a smaller _draft model_ generates a short sequence of candidate tokens (typically between 3 and 12). This draft model is usually an approximation or a lightweight auxiliary network that can run faster than the target model. The goal here is to propose multiple token sequences quickly.

### Verification Phase
In the verification phase, the larger _target model_ scores the entire draft sequence in one batched forward pass. A modified rejection sampling algorithm compares the draft and target probabilities at each position. If the target model would have been at least as likely to produce a given token, it is accepted; otherwise, it is rejected.

### Benefits
- **Latency Reduction**: By generating multiple tokens per step, speculative decoding can reduce latency by up to 2-3 times compared to standard autoregressive decoding.
- **No Change in Output Distribution**: The technique ensures that the final output distribution remains identical to that of the target model's standard decoding.

## Background

Standard autoregressive decoding in LLMs generates one token at a time, which is bottlenecked by memory bandwidth rather than arithmetic throughput. Speculative decoding leverages this property by running multiple tokens concurrently, thereby reducing overall latency without altering the output distribution.

## Open Questions
- **Optimal Draft Length**: What is the optimal length of the draft sequence for different model sizes and tasks?
- **Verification Algorithm Efficiency**: How can the verification algorithm be optimized to further reduce latency while maintaining accuracy?

## Sources

1. Leviathan, Yaniv; Kalman, Matan; Matias, Yossi (2023). "Fast Inference from Transformers via Speculative Decoding". *Proceedings of the 40th International Conference on Machine Learning (ICML)*.
2. Chen, Charlie; Borgeaud, Sebastian; Irving, Geoffrey; Lespiau, Jean-Baptiste; Sifre, Laurent; Jumper, John (2023-02-02). "Accelerating Large Language Model Decoding with Speculative Sampling". *arXiv:2302.01318*.
3. Xia, Heming; Yang, Zhe; Dong, Qingxiu; Wang, Peiyi; Li, Yongqi; Ge, Tao; Liu, Tianyu; Li, Wenjie; Sui, Zhifang (2024-06-04). "Unlocking Efficiency in Large Language Model Inference: A Comprehensive Survey of Speculative Decoding". *arXiv:2401.07851*.
4. Miao, Xupeng; Oliaro, Gabriele; Zhang, Zhihao; Cheng, Xinhao; Wang, Zeyu; Zhang, Zhengxin; Wong, Rae Ying Yee; Zhu, Alan; Yang, Lijie (2024-04-01). "SpecInfer: Accelerating Generative Large Language Model Serving with Tree-based Speculative Inference and Verification". *arXiv:2305.09781*.
5. Cai, Tianle; Li, Yuhong; Geng, Zhengyang; Peng, Hongwu; Lee, Jason D.; Chen, Deming; Dao, Tri (2024-06-14). "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads". *arXiv:2401.10774*.
6. Wikipedia contributors. Speculative decoding [online]. Available at: <https://en.wikipedia.org/wiki/Speculative_decoding> (Accessed on 2026-04-05).
7. Hugging Face blog contributors. Assisted generation [online]. Available at: <https://huggingface.co/blog/assisted-generation> (Accessed on 2026-04-05).