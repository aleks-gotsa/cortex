# Executive Summary

Continuous batching in large language model (LLM) serving significantly improves throughput while reducing latency compared to traditional request-based dynamic batching policies. This research synthesizes findings from multiple sources and highlights key aspects of continuous batching:

1. **Definition**: Continuous batching, also known as dynamic batching or iteration-level scheduling, processes requests at the granularity of iterations rather than entire requests (Figure 1). It allows for more efficient memory management by reducing fragmentation and redundant duplication.
2. **Performance Improvement**: Studies show that continuous batching can achieve up to 23x throughput improvement over naive batching methods when serving LLMs. This is particularly effective in scenarios with high variance in sequence lengths, as seen in benchmarks (Source [5]).
3. **Implementation Challenges**: While continuous batching offers significant benefits, its implementation requires careful memory management and scheduling strategies. Frameworks like vLLM leverage advanced techniques such as PagedAttention to optimize memory usage and improve performance.

# Continuous Batching in LLM Serving

## Definition of Continuous Batching
Continuous batching is a technique that processes requests at the granularity of iterations rather than entire requests (Source [1]). This approach allows for more efficient memory management by reducing fragmentation and redundant duplication. It is particularly useful when serving large language models, where each request involves multiple iterations to generate output tokens.

## How Continuous Batching Improves Performance
Continuous batching improves performance in LLMs through several mechanisms:
- **Reduced Memory Fragmentation**: By managing memory at the iteration level, continuous batching minimizes fragmentation and ensures that GPU memory is used more efficiently (Source [3], Source [4]).
- **Flexible Sharing of Key-Value Cache**: Continuous batching enables flexible sharing of key-value cache within and across requests, further reducing memory usage. This is demonstrated by vLLM's implementation using PagedAttention (Source [4]).

## Implementation Challenges
Implementing continuous batching effectively requires addressing several challenges:
- **Memory Management**: Efficiently managing GPU memory to avoid fragmentation and redundant duplication.
- **Scheduling Mechanisms**: Scheduling the execution of model iterations in a way that maximizes throughput while minimizing latency.
- **Integration with Existing Frameworks**: Integrating continuous batching into existing inference servers like Ray Serve or Hugging Face’s text-generation-inference.

# Open Questions
1. **Optimization Techniques Beyond PagedAttention**: While PagedAttention is effective, there may be other optimization techniques that can further enhance the performance of continuous batching.
2. **Scalability and Performance in Larger Models**: The effectiveness of continuous batching in serving larger models with hundreds of billions of parameters remains an open question (Source [7]).
3. **Impact on Model Accuracy**: Continuous batching might introduce minor accuracy issues due to its iterative nature, which needs further investigation.

# Sources
1. Anyscale blog: Continuous Batching in LLM Inference — Part 2. URL: <https://www.anyscale.com/blog/continuous-batching-llm-inference>
2. Anyscale blog: Continuous Batching in LLM Inference — Part 6. URL: <https://www.anyscale.com/blog/continuous-batching-llm-inference>
3. Anyscale blog: Continuous Batching in LLM Inference — Part 1. URL: <https://www.anyscale.com/blog/continuous-batching-llm-inference>
4. Kwon, W., Li, Z., Zhuang, S., Sheng, Y., Zheng, L., Yu, C.H., Gonzalez, J.E., Zhang, H., & Stoica, I. (2023). Efficient Memory Management for Large Language Model Serving with PagedAttention. arXiv:2309.06180 [cs.LG].
5. Anyscale blog: Continuous Batching in LLM Inference — Part 7. URL: <https://www.anyscale.com/blog/continuous-batching-llm-inference>
6. Wikipedia: vLLM. URL: <https://en.wikipedia.org/wiki/VLLM>
7. USENIX abstract: Orca: A Distributed Serving System for Transformer-Based Generative Models. URL: <https://www.usenix.org/conference/osdi22/presentation/yu>
8. Wikipedia: vLLM (Part 1). URL: <https://en.wikipedia.org/wiki/VLLM>
9. Wikipedia: vLLM (Part 3). URL: <https://en.wikipedia.org/wiki/VLLM>