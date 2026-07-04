# Research Document: NVIDIA Dynamo Disaggregated Inference

## Executive Summary
NVIDIA Dynamo is an open-source inference framework designed to enhance the performance and efficiency of large-scale distributed reasoning AI models. It introduces disaggregated prefill and decode inference stages, dynamic GPU scheduling, and LLM-aware request routing. Key findings include:
- **Disaggregation Benefits**: Disaggregating prefill and decode phases allows for better hardware allocation and improved scalability.
- **Dynamic Scheduling**: The NVIDIA Dynamo Planner optimizes GPU resource allocation based on real-time metrics to balance load and minimize latency.
- **Performance Enhancements**: By leveraging efficient KV transfer, dynamic scheduling, and disaggregated serving, Dynamo can significantly increase the throughput of inference requests.

## Architecture and Resource Allocation
### NVIDIA Dynamo Architecture
NVIDIA Dynamo consists of several key components:
1. **Planner**: Monitors GPU capacity metrics and application Service Level Objectives (SLOs) to decide on disaggregation or aggregation.
2. **Prefill Router**: Orchestrates the prefill phase by selecting workers based on cache overlap scores and load balancing.

### Resource Allocation
- **Disaggregated Stages**: Dynamo disaggregates the prefill and decode phases, allowing for specialized GPU allocation.
  - This suggests that traditional aggregated serving might not always be the most efficient solution (Source [1]).
- **Dynamic Scheduling**: The NVIDIA Dynamo Planner dynamically schedules GPUs based on fluctuating demand to optimize performance. This implies a more flexible approach to resource management compared to static configurations.

## Performance Benefits
### Throughput and Latency Reductions
- **Increased Throughput**: By disaggregating the prefill and decode phases, Dynamo can achieve up to 30x higher throughput when running models like DeepSeek-R1 on NVIDIA Blackwell (Source [2]).
- **Latency Optimization**: The efficient KV transfer mechanism ensures minimal inference response time. This suggests that latency is significantly reduced compared to traditional methods.

## Open Questions
- How does the NVIDIA Dynamo Planner make decisions regarding disaggregation versus aggregation?
- What are the specific metrics and SLOs used by the Dynamo Planner for decision-making?
- Are there any limitations or trade-offs associated with the disaggregated serving approach?

## Sources
1. Introducing NVIDIA Dynamo — NVIDIA Developer Blog (part 4)
2. Introducing NVIDIA Dynamo — NVIDIA Developer Blog (part 2)
3. Introducing NVIDIA Dynamo — NVIDIA Developer Blog (part 3)
4. Disaggregated Serving — NVIDIA Dynamo design docs (part 2)
5. ai-dynamo/dynamo — GitHub README (part 2)
6. ai-dynamo/dynamo — GitHub README (part 3)
7. Disaggregated Serving — NVIDIA Dynamo design docs (part 1)
8. DistServe: Disaggregating Prefill and Decoding — arXiv
9. ai-dynamo/dynamo — GitHub README (part 5)
10. ai-dynamo/dynamo — GitHub README (part 1)