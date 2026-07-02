# Executive Summary

Model quantization is a technique used to reduce the computational and memory costs of running inference by representing model weights and activations with lower precision data types, such as `int8`. This reduces energy consumption in theory but can lead to increased energy consumption in practice depending on the model size. The process involves converting high-precision floating-point numbers into lower-precision formats like `float16`, `bfloat16`, or `int8`. While quantization is beneficial for memory reduction, its impact on energy efficiency varies significantly based on factors such as model size and batch size.

This document outlines the key aspects of model quantization, including theoretical concepts, practical steps, and tradeoffs. It highlights that while quantization can reduce memory usage and potentially improve performance on certain hardware, it may also introduce accuracy degradation and increase energy consumption in some scenarios. The document concludes with open questions regarding the optimal deployment strategies for different models.

# Model Quantization

## Definition
Model quantization is a technique to reduce the computational and memory costs of running inference by representing model weights and activations using lower-precision data types, such as `int8` instead of the usual 32-bit floating point (`float32`). This reduces energy consumption in theory but can lead to increased energy consumption in practice depending on the model size.

### Tradeoffs
1. **Memory Reduction**: Lower precision formats like `int8` require less memory storage, which is beneficial for deployment on devices with limited resources.
2. **Energy Efficiency**: In theory, lower precision operations consume less energy than high-precision ones. However, in practice, this may not always hold true due to overheads associated with dequantization and quantization processes.

## Practical Steps
To effectively quantize a model to `int8`, the following steps can be followed:
1. **Choose Operators**: Identify operators that dominate computation time (e.g., linear projections and matrix multiplications).
2. **Post-Training Dynamic Quantization**: Try this method first as it is faster.
3. **Post-Training Static Quantization**: If dynamic quantization is not fast enough, try static quantization which can be faster but may result in a drop in accuracy.
4. **Calibration Techniques**: Apply observers to the model where you want to quantize and choose an appropriate calibration technique.
5. **Model Conversion**: Remove observers and convert `float32` operators to their `int8` counterparts.
6. **Accuracy Evaluation**: Assess if the accuracy is sufficient; if not, consider Quantization-Aware Training (QAT).

## Energy Efficiency
The relationship between quantization and energy consumption is more nuanced in practice:
- For large models (`≥5B parameters`), NF4 quantization achieves near-FP16 energy consumption with significant memory savings.
- For small models (`<3B parameters`), NF4 quantization can increase energy consumption by 25–56% despite achieving 75% memory compression due to dequantization overhead.
- INT8 mixed-precision introduces a 17–33% energy overhead compared to FP16, justifying the cost for maintaining model accuracy.

## Supported Tools
🤗 Optimum provides APIs to perform quantization using different tools:
- `optimum.onnxruntime` for ONNX models with ONNX Runtime.
- `optimum.intel` for 🤗 Transformers models while respecting accuracy and latency constraints.
- `optimum.fx` for PyTorch graph-mode quantization of 🤗 Transformers models, offering more flexibility but requiring more work.
- `optimum.gptq` for LLM models with GPTQ.

# Open Questions
1. **Optimal Deployment Strategies**: What are the optimal deployment strategies for different model sizes and hardware generations?
2. **Energy Consumption Variability**: How does energy consumption vary across different precision formats and batch sizes?

# Sources

1. Quantization concepts — Hugging Face Optimum docs (part 1) [https://huggingface.co/docs/optimum/concept_guides/quantization]
2. Quantization concepts — Hugging Face Optimum docs (part 8) [https://huggingface.co/docs/optimum/concept_guides/quantization]
3. Quantization concepts — Hugging Face Optimum docs (part 9) [https://huggingface.co/docs/optimum/concept_guides/quantization]
4. Quantization concepts — Hugging Face Optimum docs (part 7) [https://huggingface.co/docs/optimum/concept_guides/quantization]
5. A White Paper on Neural Network Quantization — arXiv [https://arxiv.org/abs/2106.08295]