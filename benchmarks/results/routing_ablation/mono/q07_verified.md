# Research Document: How Does Triton Inference Server Work?

## Executive Summary

Triton Inference Server, an open-source software from NVIDIA, streamlines AI inference by supporting multiple deep learning and machine learning frameworks across various hardware platforms. This document outlines the architecture of Triton Inference Server, its model deployment mechanisms, and key components involved in the inference process.

## Architecture and Model Deployment

### Architecture Overview
Triton Inference Server features a modular design that allows for flexibility and customization (Source [1], Source [2]). The server's high-level architecture includes a model repository where models are stored. These models can be accessed via HTTP/REST, gRPC, or C API requests (Source [3]).

### Model Deployment
Models are deployed by placing them in the specified model repository. Triton supports multiple execution engines called backends, such as TensorRT, PyTorch, ONNX, OpenVINO, Python, and more (Source [4], Source [5]). The choice of backend depends on the target platform's support (Source [6]).

## Inference Process

### Key Components
The inference process in Triton involves several key components:
- **Model Repository**: A file-system based repository where models are stored.
- **Scheduler**: Manages and schedules inference requests for each model. It can perform batching of requests to optimize performance (Source [7]).
- **Batcher**: Handles batch processing, which is crucial for real-time and batched queries (Source [7]).
- **Client Libraries**: Provide APIs for sending inference requests to Triton.

### Inference Workflow
1. A client application sends an inference request to Triton using HTTP/REST or gRPC protocols.
2. The server routes the request to the appropriate model scheduler based on the model configuration.
3. The scheduler batches and schedules the requests, optimizing performance through dynamic batching (Source [7]).
4. The backend processes the requests, leveraging the chosen execution engine (e.g., TensorRT, PyTorch).
5. Results are returned to the client.

## Open Questions

- **Detailed Backend Implementation**: While Triton supports multiple backends, specific implementation details for each backend are not fully detailed in the provided sources.
- **Customization and Extensibility**: The extent of customization options available through custom backends and pre/post-processing operations is not extensively covered.
- **Performance Optimization Tools**: Although tools like Performance Analyzer and Model Analyzer exist, their full capabilities and integration with Triton's workflow need further exploration.

## Sources

Source [1]: Triton Inference Server — NVIDIA user guide index. URL: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html
Source [2]: Triton architecture — NVIDIA Triton user guide. URL: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/architecture.html
Source [3]: triton-inference-server/server — GitHub README (part 4). URL: https://github.com/triton-inference-server/server
Source [4]: triton-inference-server/server — GitHub README (part 1). URL: https://github.com/triton-inference-server/server
Source [5]: triton-inference-server/server — GitHub README (part 3). URL: https://github.com/triton-inference-server/server
Source [6]: triton-inference-server/server — GitHub README (part 2). URL: https://github.com/triton-inference-server/server
Source [7]: Model repository — NVIDIA Triton user guide. URL: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/model_repository.html