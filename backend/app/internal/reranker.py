import os
import threading
from typing import Any, Dict, List, Optional

from app.internal.embedding_manager import EMBEDDING_CACHE_DIR

DEFAULT_RERANK_MODEL = os.getenv("RERANK_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2")

_reranker = None
_lock = threading.Lock()


def is_enabled() -> bool:
    return os.getenv("RERANK_ENABLED", "true").lower() in ("1", "true", "yes", "on")


def _get_reranker():
    global _reranker
    if _reranker is None:
        with _lock:
            if _reranker is None:
                from fastembed.rerank.cross_encoder import TextCrossEncoder

                _reranker = TextCrossEncoder(
                    model_name=DEFAULT_RERANK_MODEL,
                    cache_dir=EMBEDDING_CACHE_DIR,
                )
    return _reranker


def rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int,
    document_key: str = "document",
) -> List[Dict[str, Any]]:
    """
    Reorders candidate chunks with a cross-encoder.

    Candidates are dicts shaped like {"id", "document", "metadata", "distance"}.
    On any failure (model missing, disabled, empty input) the original vector
    order is preserved so retrieval never breaks because of the reranker.
    """
    if top_k <= 0 or not candidates:
        return candidates[:max(top_k, 0)]
    if not is_enabled():
        return candidates[:top_k]

    try:
        model = _get_reranker()
        scores = list(model.rerank(query, [c[document_key] for c in candidates]))
        scored = sorted(
            zip(candidates, scores),
            key=lambda pair: pair[1],
            reverse=True,
        )
        result = []
        for candidate, score in scored[:top_k]:
            candidate = dict(candidate)
            candidate["rerank_score"] = float(score)
            result.append(candidate)
        return result
    except Exception as e:  # pragma: no cover - depends on optional model
        print(f"Reranker unavailable, falling back to vector order: {e}")
        return candidates[:top_k]
