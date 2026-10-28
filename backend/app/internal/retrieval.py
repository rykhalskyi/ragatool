import os
from typing import Any, Dict, List, Optional

from app.internal import reranker, vector_store
from app.internal.embedding_manager import embed_query

RESULT_KEYS = ("ids", "documents", "metadatas", "distances")


def _env_bool(name: str, default_value: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default_value
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str) -> Optional[int]:
    value = os.getenv(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _load_settings() -> tuple[bool, Optional[int]]:
    """
    Reads retrieval settings from the database (editable in the Settings view).

    Environment variables act as fallbacks when the DB rows are missing, so
    container-only deployments keep working.
    """
    rerank_enabled = _env_bool("RERANK_ENABLED", True)
    fetch_k = _env_int("RETRIEVAL_FETCH_K")

    try:
        from app.database import get_db_connection
        from app.internal.settings_manager import SettingsManager
        from app.schemas.setting import SettingsName

        db = get_db_connection()
        try:
            manager = SettingsManager(db)
            rerank_enabled = manager.get_bool(SettingsName.RERANK_ENABLED, rerank_enabled)
            configured_fetch = manager.get_setting(SettingsName.RETRIEVAL_FETCH_K)
            if configured_fetch is not None:
                try:
                    fetch_k = int(configured_fetch)
                except (TypeError, ValueError):
                    pass
        finally:
            db.close()
    except Exception as e:
        print(f"Could not load retrieval settings, using defaults: {e}")

    return rerank_enabled, fetch_k


def _fetch_k(n_results: int, configured: Optional[int] = None) -> int:
    if configured:
        return max(n_results, configured)
    return max(n_results, n_results * 4, 20)


def _empty_results() -> Dict[str, Any]:
    return {key: [] for key in RESULT_KEYS}


def _to_candidates(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    ids = (results.get("ids") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    candidates = []
    for index, chunk_id in enumerate(ids):
        candidates.append(
            {
                "id": chunk_id,
                "document": documents[index] if index < len(documents) else None,
                "metadata": metadatas[index] if index < len(metadatas) else None,
                "distance": distances[index] if index < len(distances) else None,
            }
        )
    return candidates


def _to_chroma_shape(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "ids": [[candidate["id"] for candidate in candidates]],
        "documents": [[candidate["document"] for candidate in candidates]],
        "metadatas": [[candidate["metadata"] for candidate in candidates]],
        "distances": [[candidate["distance"] for candidate in candidates]],
    }


def retrieve(
    collection_name: str,
    query_text: str,
    n_results: int = 10,
    fetch_k: Optional[int] = None,
    rerank: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Single retrieval path used by the HTTP API and the MCP tools.

    1. Embed the query with the collection's own embedding model.
    2. Fetch a wider candidate set from Chroma (cosine).
    3. Optionally reorder candidates with a cross-encoder.
    """
    n_results = max(1, int(n_results))
    rerank_setting, fetch_k_setting = _load_settings()
    collection = vector_store.get_collection(collection_name)

    count = collection.count()
    if not count:
        return {"status": "success", "results": _empty_results()}

    embedding = embed_query(query_text, vector_store.get_collection_embedding_model(collection))
    requested = fetch_k or _fetch_k(n_results, fetch_k_setting)
    requested = max(n_results, min(requested, count))

    results = collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=requested,
        include=["documents", "metadatas", "distances"],
    )

    candidates = _to_candidates(results)
    should_rerank = rerank_setting if rerank is None else rerank
    if should_rerank and len(candidates) > n_results:
        candidates = reranker.rerank(query_text, candidates, top_k=n_results)
    else:
        candidates = candidates[:n_results]

    return {"status": "success", "results": _to_chroma_shape(candidates)}
