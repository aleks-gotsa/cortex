"""Triton Inference Server HTTP client for BGE embeddings."""

import logging

import httpx
import numpy as np

from dynamo.config import dynamo_settings

logger = logging.getLogger(__name__)


class TritonEmbeddingClient:
    """
    Replaces local SentenceTransformer with Triton HTTP inference.
    API: POST {DYNAMO_TRITON_URL}/v2/models/bge-embeddings/infer

    Triton request format (HTTP JSON):
    {
      "inputs": [{
        "name": "TEXT",
        "shape": [N, 1],
        "datatype": "BYTES",
        "data": ["text1", "text2", ...]
      }]
    }

    Triton response format:
    {
      "outputs": [{
        "name": "EMBEDDINGS",
        "shape": [N, 384],
        "datatype": "FP32",
        "data": [flat list of floats]
      }]
    }
    """

    def __init__(self) -> None:
        self._url = f"{dynamo_settings.DYNAMO_TRITON_URL}/v2/models/bge-embeddings/infer"

    def encode(
        self,
        texts: list[str] | str,
        normalize_embeddings: bool = True,
    ) -> np.ndarray:
        """Synchronous encode — matches SentenceTransformer interface.

        WARNING: Do NOT call from within a running event loop (use encode_async instead).
        """
        import asyncio

        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False

        result = asyncio.run(self._encode_impl(texts, normalize_embeddings))
        return result[0] if single else result

    async def encode_async(
        self,
        texts: list[str] | str,
        normalize: bool = True,
    ) -> np.ndarray:
        """Async encode — use this from within a running event loop."""
        if isinstance(texts, str):
            texts = [texts]
        return await self._encode_impl(texts, normalize)

    async def _encode_impl(self, texts: list[str], normalize: bool) -> np.ndarray:
        payload = {
            "inputs": [{
                "name": "TEXT",
                "shape": [len(texts), 1],
                "datatype": "BYTES",
                "data": texts,
            }]
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self._url, json=payload)
            response.raise_for_status()
            data = response.json()

        flat = data["outputs"][0]["data"]
        embeddings = np.array(flat, dtype=np.float32).reshape(len(texts), -1)

        if normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            embeddings = embeddings / norms

        return embeddings


def get_embedding_model():
    """
    Returns TritonEmbeddingClient if Triton is enabled, else falls back
    to local SentenceTransformer. Drop-in replacement.
    """
    if dynamo_settings.DYNAMO_ENABLED and dynamo_settings.DYNAMO_MODE == "real":
        logger.info("Using Triton embedding server at %s", dynamo_settings.DYNAMO_TRITON_URL)
        return TritonEmbeddingClient()
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("BAAI/bge-small-en-v1.5")
