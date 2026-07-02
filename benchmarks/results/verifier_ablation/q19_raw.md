# Research Document: How Does PagedAttention Improve KV Cache Efficiency?

## Executive Summary

PagedAttention is a novel attention algorithm that significantly improves key-value (KV) cache efficiency for large language models (LLMs). By partitioning the KV cache into blocks and managing these blocks in a manner inspired by virtual memory, PagedAttention reduces memory fragmentation and allows for efficient sharing of cached data. This approach leads to near-optimal memory usage, increased GPU utilization, and higher throughput compared to traditional methods.

## 1. Introduction to PagedAttention

PagedAttention is an attention algorithm designed to optimize the key-value cache (KV cache) management in LLMs [1][2]. It addresses the challenge of managing large amounts of memory required for storing keys and values during autoregressive decoding, which can lead to significant memory fragmentation and inefficiencies. The core idea behind PagedAttention is to partition the KV cache into logical blocks that are mapped to physical memory spaces in a non-contiguous manner [1][2].

### 1.1 Key Concepts

- **Logical Blocks**: These represent fixed-size segments of tokens within a sequence.
- **Physical Blocks**: These correspond to actual memory locations where keys and values are stored, which can be allocated on demand.

## 2. Mechanism of PagedAttention

PagedAttention operates by dividing the KV cache into blocks that do not need to be contiguous in physical memory [1][2]. This allows for more flexible management of cached data, similar to how virtual memory works in operating systems. The key steps are:

- **Block Partitioning**: Each sequence's KV cache is divided into fixed-size logical blocks.
- **Non-contiguous Memory Allocation**: Physical blocks can be allocated and deallocated as needed, leading to efficient use of memory.

### 2.1 Example Generation Process

During the generation process, PagedAttention identifies and fetches necessary blocks efficiently [1]. This ensures that only relevant data is loaded into memory, reducing waste and improving overall performance.

## 3. Benefits of PagedAttention

PagedAttention offers several advantages over traditional methods:

- **Near-optimal Memory Usage**: By minimizing fragmentation, PagedAttention reduces memory waste to under 4% in practice [1].
- **Flexible Sharing**: It enables efficient sharing of cached data across multiple sequences and requests, further reducing memory usage.
- **Increased Throughput**: The improved memory management allows for more sequences to be batched together, leading to higher throughput.

## 4. Open Questions

- How does PagedAttention handle the overhead associated with block table management?
- What are the trade-offs between using PagedAttention and other memory optimization techniques?

## 5. Sources

1. vLLM: Easy, Fast, and Cheap LLM Serving — vLLM blog (part 2) [1]
2. Efficient Memory Management for LLM Serving with PagedAttention — arXiv [2]
3. vLLM: Easy, Fast, and Cheap LLM Serving — vLLM blog (part 1) [3]
4. vLLM — Wikipedia (part 2) [4]