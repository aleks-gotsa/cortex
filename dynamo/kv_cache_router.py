"""Session-level KV-cache routing for Dynamo worker instances."""

import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KVCacheRouter:
    """
    Routes research sessions to Dynamo worker instances based on
    query similarity, maximizing KV-cache reuse.

    In real Dynamo: worker instances maintain their KV cache.
    Routing the same query to the same instance = cache hit.
    This router tracks active sessions and assigns sticky routing.

    For now: implements consistent hashing on query prefix.
    Real Dynamo integration: replace _get_instance_id with
    Dynamo's worker registry API when available.
    """

    def __init__(self, num_workers: int = 2) -> None:
        self._num_workers = num_workers
        self._session_map: dict[str, int] = {}
        self._hit_count = 0
        self._miss_count = 0

    def get_worker_instance(self, query: str, research_id: str) -> int:
        """Return worker instance index (0 to num_workers-1)."""
        query_prefix = query[:50].lower().strip()
        prefix_hash = hashlib.md5(query_prefix.encode()).hexdigest()[:8]

        if prefix_hash in self._session_map:
            self._hit_count += 1
            instance = self._session_map[prefix_hash]
            logger.info("[KVCache] HIT: query prefix=%r -> worker %d", query_prefix, instance)
            return instance

        # Assign new worker via consistent hashing on research_id
        instance = int(hashlib.md5(research_id.encode()).hexdigest(), 16) % self._num_workers
        self._session_map[prefix_hash] = instance
        self._miss_count += 1
        logger.info("[KVCache] MISS: query prefix=%r -> worker %d (assigned)", query_prefix, instance)
        return instance

    def get_stats(self) -> dict:
        total = self._hit_count + self._miss_count
        return {
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": self._hit_count / total if total > 0 else 0.0,
            "active_sessions": len(self._session_map),
        }

    def clear(self) -> None:
        self._session_map.clear()
        self._hit_count = 0
        self._miss_count = 0


# Module-level singleton
_router: Optional[KVCacheRouter] = None


def get_kv_router() -> KVCacheRouter:
    global _router
    if _router is None:
        _router = KVCacheRouter(num_workers=2)
    return _router
