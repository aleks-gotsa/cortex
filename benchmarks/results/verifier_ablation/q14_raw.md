# Executive Summary

In 2026, the landscape of open-source large language models (LLMs) has seen significant advancements. The Qwen3 series from QwenLM stands out as a prominent example, with multiple model sizes and enhanced capabilities such as handling ultra-long inputs up to one million tokens. This progress is supported by various inference frameworks like SGLang, vLLM, TensorRT-LLM, and LightLLM, which enable efficient deployment across different hardware platforms.

The Open LLM Leaderboard from Hugging Face highlights the performance of these models on diverse reasoning tasks, with Qwen3 performing well in both IFEval and Big Bench Hard (BBH) benchmarks. However, there are still areas for improvement, particularly in multi-step tool use and reasoning capabilities, which may be suboptimal due to preprocessing issues.

# Current State of Open Source LLMs

## Model Development
Qwen3 from QwenLM has been actively developed since 2024, with multiple model sizes released. The latest versions support ultra-long inputs up to one million tokens and include both thinking and instruct modes (Source [2], [10]). These models are supported by various inference frameworks such as SGLang, vLLM, TensorRT-LLM, and LightLLM, which facilitate deployment on different hardware platforms.

## Performance Benchmarks
The Qwen3 series performs well in the IFEval and BBH benchmarks (Source [1], [12]). Specifically:
- **IFEval**: Qwen3 demonstrates high accuracy at both instance and prompt levels.
- **BBH**: The model shows strong performance across various subtasks, achieving normalized accuracy.

## Deployment Frameworks
Several inference frameworks support the deployment of Qwen3 models. These include SGLang, vLLM, TensorRT-LLM, and LightLLM (Source [2], [6]). Each framework offers unique advantages:
- **SGLang**: Supports multi-token prediction and is recommended for its performance.
- **vLLM**: Offers high throughput and memory efficiency with support for tensor parallelism.
- **TensorRT-LLM**: Provides optimized attention kernels and quantization options, particularly on NVIDIA GPUs.
- **LightLLM**: Supports efficient single-node or multi-node deployment.

## Community Support
The Qwen3 models are available through ModelScope, which provides a Python API similar to Hugging Face's Transformers. This makes it easier for users in mainland China to access the models (Source [8]).

# Open Questions

1. **Multi-Step Tool Use**: The quality of multi-step tool use with Qwen3 thinking models may be suboptimal due to preprocessing issues, which require further optimization.
2. **Training Costs and Efficiency**: While DeepSeek-V3 has achieved significant training efficiency through FP8 mixed precision training, the exact costs and detailed methodologies are not fully documented (Source [9], [10]).
3. **Community Involvement**: The current state of community involvement in developing and maintaining these models is unclear, as evidenced by limited documentation and contributions.

# Sources

[1] Open LLM Leaderboard — Hugging Face docs. URL: https://huggingface.co/docs/leaderboards/open_llm_leaderboard/about
[2] QwenLM/Qwen3 — GitHub README (part 4). URL: https://github.com/QwenLM/Qwen3
[3] List of large language models — Wikipedia. URL: https://en.wikipedia.org/wiki/List_of_large_language_models
[4] QwenLM/Qwen3 — GitHub README (part 10). URL: https://github.com/QwenLM/Qwen3
[5] QwenLM/Qwen3 — GitHub README (part 9). URL: https://github.com/QwenLM/Qwen3
[6] deepseek-ai/DeepSeek-V3 — GitHub README (part 6). URL: https://github.com/deepseek-ai/DeepSeek-V3
[7] deepseek-ai/DeepSeek-V3 — GitHub README (part 4). URL: https://github.com/deepseek-ai/DeepSeek-V3
[8] QwenLM/Qwen3 — GitHub README (part 7). URL: https://github.com/QwenLM/Qwen3
[9] deepseek-ai/DeepSeek-V3 — GitHub README (part 7). URL: https://github.com/deepseek-ai/DeepSeek-V3
[10] deepseek-ai/DeepSeek-V3 — GitHub README (part 2). URL: https://github.com/deepseek-ai/DeepSeek-V3
[11] Open LLM Leaderboard — Hugging Face docs (part 2). URL: https://huggingface.co/docs/leaderboards/open_llm_leaderboard/about
[12] Open LLM Leaderboard — Hugging Face docs (part 3). URL: https://huggingface.co/docs/leaderboards/open_llm_leaderboard/about