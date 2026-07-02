# Research Document: NVIDIA Dynamo Disaggregated Inference

## Executive Summary
NVIDIA Dynamo is an open-source inference framework designed to enhance the performance and efficiency of large-scale distributed AI model deployments, particularly for reasoning models. It introduces disaggregated prefill and decode inference stages, dynamic GPU scheduling, and LLM-aware request routing to optimize throughput and minimize latency. Key features include efficient key-value (KV) transfer between GPUs, intelligent load balancing, and automatic scaling based on application service level objectives (SLOs). This document synthesizes the core mechanisms of NVIDIA Dynamo's disaggregated inference approach.

## 1. Disaggregated Inference Mechanism
### Prefill and Decode Stages
NVIDIA Dynamo disaggregates the prefill and decode stages of LLM requests, allowing for specialized hardware allocation to optimize performance (Source [4], Source [8]). The prefill engine computes the KV cache, which is then transferred non-blocking to the decode engine. This separation enables better resource utilization and reduces interference between phases.

### Efficient Key-Value Transfer
Dynamo leverages NIXL to transfer the KV cache directly from VRAM of the prefill GPU to that of the decode GPU (Source [4]). The transfer is non-blocking, allowing forward passes on other requests during the transfer process. This mechanism ensures minimal latency and maximizes throughput.

### Router Orchestration
The disaggregated serving flow is orchestrated by the `PrefillRouter`, which selects a prefill worker based on KV-aware routing or simple load balancing (Source [4]). The router then sends the prefill request to the selected worker, computes the KV cache, and returns metadata for transfer. The decode engine subsequently uses this information to process the request.

## 2. Dynamic Scheduling and Load Balancing
### NVIDIA Dynamo Planner
NVIDIA Dynamo Planner continuously monitors GPU capacity metrics in distributed inference environments (Source [1]). It combines these with application-specific Service Level Objectives (SLOs) such as Time To First Token (TTFT) and Inter-token Latency (ITL) to make informed decisions on whether to serve requests with or without disaggregation. The planner also decides if additional GPUs should be added to either phase, ensuring efficient resource allocation.

## 3. Open Questions
- **How does the NVIDIA Dynamo Planner handle edge cases where both prefill and decode GPUs are underutilized?**
- **What is the impact of varying input sequence lengths (ISLs) on the efficiency of disaggregated inference?**
