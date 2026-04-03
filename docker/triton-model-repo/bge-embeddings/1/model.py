"""Triton Python backend for BAAI/bge-small-en-v1.5 embeddings."""

import json
import numpy as np

try:
    import triton_python_backend_utils as pb_utils
except ImportError:
    pb_utils = None

from sentence_transformers import SentenceTransformer


class TritonPythonModel:
    """Triton Python backend that serves BGE embeddings."""

    def initialize(self, args: dict) -> None:
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    def execute(self, requests: list) -> list:
        responses = []

        for request in requests:
            text_tensor = pb_utils.get_input_tensor_by_name(request, "TEXT")
            texts = [t.decode("utf-8") if isinstance(t, bytes) else t for t in text_tensor.as_numpy().flatten()]

            embeddings = self.model.encode(texts, normalize_embeddings=True)
            embeddings = np.array(embeddings, dtype=np.float32)

            out_tensor = pb_utils.Tensor("EMBEDDINGS", embeddings)
            responses.append(pb_utils.InferenceResponse(output_tensors=[out_tensor]))

        return responses

    def finalize(self) -> None:
        pass
