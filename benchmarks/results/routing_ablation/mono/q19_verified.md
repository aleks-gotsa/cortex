# Research Document: How Does PagedAttention Improve KV Cache Efficiency?

## Executive Summary

PagedAttention is an innovative attention algorithm that enhances key-value (KV) cache efficiency by partitioning the cache into blocks and managing them using a block table, inspired by virtual memory techniques. This mechanism allows for non-contiguous storage of keys and values, leading to reduced memory fragmentation and improved utilization. The implementation of PagedAttention in vLLM has demonstrated significant performance benefits, including near-optimal memory usage, efficient memory sharing, and increased throughput.

## 1. Mechanism of PagedAttention

### Partitioning the KV Cache into Blocks
PagedAttention partitions the key-value cache of each sequence into blocks (Figure 1). Each block contains keys and values for a fixed number of tokens. This partitioning enables more flexible management of memory, similar to how virtual memory manages physical pages in an operating system.

**Mechanism:**
- **Logical vs Physical Blocks:** The logical blocks are mapped to non-contiguous physical blocks via a block table.
- **Memory Allocation on Demand:** Physical blocks are allocated as new tokens are generated, ensuring efficient use of memory.

### Example Generation Process
During the generation process, PagedAttention identifies and fetches necessary blocks efficiently. This approach minimizes memory waste, particularly in the last block of a sequence (Figure 2). In practice, this results in near-optimal memory usage with only under 4% wasted memory.

**Inference:** The non-contiguous storage mechanism reduces fragmentation and improves overall memory efficiency.

## 2. Utilization of KV Cache

### Efficient Memory Sharing
PagedAttention facilitates efficient memory sharing through its block table (Figure 3). This is particularly useful in scenarios where multiple output sequences are generated from the same prompt, such as parallel sampling.

**Mechanism:**
- **Block Table:** Similar to how processes share physical pages, different sequences can share computation and memory for prompts.
- **Flexible Sharing:** The block table allows for flexible sharing of key-value pairs across sequences.

### Performance Benefits
The efficient management of KV cache through PagedAttention leads to several performance benefits:
1. **Near-Zero Memory Waste:** By minimizing fragmentation, the system achieves near-optimal memory usage.
2. **Increased Throughput:** Enhanced memory efficiency enables batching more sequences together and increasing GPU utilization, thereby significantly boosting throughput.

**Inference:** The ability to share key-value pairs across sequences further reduces memory overhead and improves overall performance.

## 3. Open Questions
- **Fragmentation Management:** How does PagedAttention handle fragmentation in the KV cache?
- **Block Table Design:** What are the specific design considerations for the block table used by PagedAttention?
- **Scalability:** Can PagedAttention be scaled to support larger models and longer sequences?
