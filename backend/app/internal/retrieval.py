import os
from typing import Any, Dict, List, Optional

from app.internal import reranker, vector_store
from app.internal.embedding_manager import embed_query

RESULT_KEYS = ("ids", "documents", "metadatas", "distances")


def _fetch_k(n_results: int) -> int:
    configured = os.getenv("RETRIEVAL_FETCH_K")
    if configured:
        try:
            return max(n_results, int(configured))
        except ValueError:
            pass
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
    collection = vector_store.get_collection(collection_name)

    count = collection.count()
    if not count:
        return {"status": "success", "results": _empty_results()}

    embedding = embed_query(query_text, vector_store.get_collection_embedding_model(collection))
    requested = fetch_k or _fetch_k(n_results)
    requested = max(n_results, min(requested, count))

    results = collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=requested,
        include=["documents", "metadatas", "distances"],
    )

    candidates = _to_candidates(results)
    should_rerank = reranker.is_enabled() if rerank is None else rerank
    if should_rerank and len(candidates) > n_results:
        candidates = reranker.rerank(query_text, candidates, top_k=n_results)
    else:
        candidates = candidates[:n_results]

    return {"status": "success", "results": _to_chroma_shape(candidates)}
