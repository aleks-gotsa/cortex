"""Qdrant vector memory — store and recall prior research chunks."""

import logging
import re
import uuid
from datetime import datetime, timezone

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Module-level singletons ──────────────────────────────────────────────────

_embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
_qdrant = AsyncQdrantClient(url=settings.QDRANT_URL)


# ── Collection management ────────────────────────────────────────────────────


async def ensure_collection() -> None:
    """Create the research collection if it does not already exist."""
    name = settings.QDRANT_COLLECTION
    if await _qdrant.collection_exists(name):
        return
    await _qdrant.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    logger.info("Created Qdrant collection %r", name)


# ── Chunking ─────────────────────────────────────────────────────────────────

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _chunk_document(text: str, max_tokens: int = 500) -> list[str]:
    """Split *text* into chunks of roughly *max_tokens* words each.

    Strategy:
    1. Split on paragraph boundaries (``\\n\\n``).
    2. Merge consecutive small paragraphs until approaching *max_tokens*.
    3. Split any single paragraph exceeding *max_tokens* at sentence boundaries.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buffer: list[str] = []
    buffer_len = 0

    for para in paragraphs:
        para_len = len(para.split())

        # Oversized single paragraph — flush buffer then split by sentence.
        if para_len > max_tokens:
            if buffer:
                chunks.append("\n\n".join(buffer))
                buffer, buffer_len = [], 0

            sentences = _SENTENCE_SPLIT.split(para)
            sent_buf: list[str] = []
            sent_len = 0
            for sent in sentences:
                s_len = len(sent.split())
                if sent_len + s_len > max_tokens and sent_buf:
                    chunks.append(" ".join(sent_buf))
                    sent_buf, sent_len = [], 0
                sent_buf.append(sent)
                sent_len += s_len
            if sent_buf:
                chunks.append(" ".join(sent_buf))
            continue

        # Would exceed budget — flush buffer first.
        if buffer_len + para_len > max_tokens and buffer:
            chunks.append("\n\n".join(buffer))
            buffer, buffer_len = [], 0

        buffer.append(para)
        buffer_len += para_len

    if buffer:
        chunks.append("\n\n".join(buffer))

    return chunks


# ── Public API ───────────────────────────────────────────────────────────────


async def store_research(research_id: str, query: str, document: str) -> int:
    """Chunk, embed, and upsert *document* into Qdrant. Return chunk count."""
    await ensure_collection()

    chunks = _chunk_document(document)
    if not chunks:
        return 0

    embeddings = _embed_model.encode(chunks, normalize_embeddings=True).tolist()
    now = datetime.now(timezone.utc).isoformat()

    points = [
        PointStruct(
            id=uuid.uuid4().hex,
            vector=vec,
            payload={
                "research_id": research_id,
                "query": query,
                "date": now,
                "chunk_index": idx,
                "text": text,
            },
        )
        for idx, (text, vec) in enumerate(zip(chunks, embeddings, strict=True))
    ]

    await _qdrant.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=points,
    )
    logger.info(
        "Stored %d chunks for research %s in %s",
        len(points),
        research_id,
        settings.QDRANT_COLLECTION,
    )
    return len(points)


async def recall(query: str, top_k: int = 5) -> list[str]:
    """Return the *top_k* most relevant prior-research chunks for *query*."""
    await ensure_collection()

    vector = _embed_model.encode(query, normalize_embeddings=True).tolist()

    response = await _qdrant.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=vector,
        limit=top_k,
    )

    if not response.points:
        return []

    texts = [pt.payload["text"] for pt in response.points if pt.payload]
    logger.info("Recalled %d chunks for query %r", len(texts), query[:80])
    return texts
