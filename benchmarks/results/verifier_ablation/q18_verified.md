# Tensor Parallelism in Distributed LLM Inference: A Comprehensive Research Document

## Executive Summary
This document synthesizes information on tensor parallelism in distributed large language model (LLM) inference. Key findings include:
- Tensor parallelism is a technique used to distribute the computation of a single layer across multiple GPUs, enabling training of very large models.
- Megatron-LM employs an intra-layer model parallel approach that does not require new compiler or library changes and can be fully implemented with minimal modifications in native PyTorch. This method has been successfully applied to train transformer-based models up to 8.3 billion parameters using 512 GPUs, achieving high efficiency.
- The technique is orthogonal and complimentary to pipeline model parallelism, allowing for flexible scaling of training across multiple GPUs.

## Sections

### What is Tensor Parallelism in Distributed LLM Inference?
Tensor parallelism involves distributing the computation of a single layer across multiple GPUs. This approach enables the training of very large models by breaking down the computational load into smaller parts that can be processed concurrently. According to [1], this technique has been successfully implemented using Megatron-LM, which provides an efficient intra-layer model parallel approach.

### Implementation and Application
Megatron-LM uses a simple, efficient intra-layer model parallelism strategy that does not require new compiler or library changes. This method is orthogonal and complimentary to pipeline model parallelism, allowing for flexible scaling of training across multiple GPUs [1]. The implementation can be fully realized with the insertion of a few communication operations in native PyTorch.

### Performance and Scalability
The approach has been demonstrated through the successful training of transformer-based models up to 8.3 billion parameters using 512 GPUs, achieving high efficiency. For instance, an 8.3 billion parameter GPT-2 model was trained with a sustained performance of 15.1 PetaFLOPs across the entire application [1].

### Open Questions
- What are the specific communication operations required for tensor parallelism in Megatron-LM?
- How does tensor parallelism interact with other parallelism strategies like pipeline parallelism?

## Sources

[1] Shoeybi, M., Patwary, M., Puri, R., LeGresley, P., Casper, J., & Catanzaro, B. (2019). Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism. *arXiv preprint arXiv:1909.08053*. https://arxiv.org/abs/1909.08053
