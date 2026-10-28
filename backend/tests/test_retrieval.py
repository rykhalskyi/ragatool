import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from app.internal import retrieval


def _collection():
    collection = MagicMock()
    collection.count.return_value = 100
    collection.metadata = {"embedding_model": "BAAI/bge-small-en-v1.5"}
    collection.query.return_value = {
        "ids": [["a", "b", "c"]],
        "documents": [["doc a", "doc b", "doc c"]],
        "metadatas": [[{}, {}, {}]],
        "distances": [[0.1, 0.2, 0.3]],
    }
    return collection


@patch("app.internal.retrieval._load_settings", return_value=(False, 15))
@patch("app.internal.retrieval.vector_store.get_collection")
@patch("app.internal.retrieval.embed_query", return_value=np.array([0.1, 0.2]))
@patch("app.internal.retrieval.reranker.rerank")
def test_retrieve_uses_fetch_k_and_skips_rerank(
    mock_rerank, mock_embed, mock_get_collection, mock_settings
):
    collection = _collection()
    mock_get_collection.return_value = collection

    result = retrieval.retrieve("test_collection", "query", n_results=3)

    assert collection.query.call_args.kwargs["n_results"] == 15
    mock_rerank.assert_not_called()
    assert result["results"]["ids"] == [["a", "b", "c"]]


@patch("app.internal.retrieval._load_settings", return_value=(True, 15))
@patch("app.internal.retrieval.vector_store.get_collection")
@patch("app.internal.retrieval.embed_query", return_value=np.array([0.1, 0.2]))
@patch("app.internal.retrieval.reranker.rerank")
def test_retrieve_reranks_when_enabled(
    mock_rerank, mock_embed, mock_get_collection, mock_settings
):
    collection = _collection()
    mock_get_collection.return_value = collection
    mock_rerank.return_value = [
        {"id": "a", "document": "doc a", "metadata": {}, "distance": 0.1}
    ]

    retrieval.retrieve("test_collection", "query", n_results=2)

    mock_rerank.assert_called_once()
    assert mock_rerank.call_args.kwargs["top_k"] == 2
