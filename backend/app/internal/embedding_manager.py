import os
from typing import Dict, Optional

from fastembed import TextEmbedding

DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR", ".fastembed")

_embedders: Dict[str, TextEmbedding] = {}


def resolve_embedding_model(model_name: Optional[str]) -> str:
    """
    Accepts a HuggingFace-style model id (contains "/") and otherwise falls
    back to the configured default. This keeps legacy values such as
    "some_model" from being treated as embedding models.
    """
    if model_name and "/" in model_name:
        return model_name
    return DEFAULT_EMBEDDING_MODEL


def get_embedder(model_name: Optional[str] = None) -> TextEmbedding:
    """
    Returns a cached TextEmbedding instance for the requested model.

    The model is loaded lazily on first use and cached per model name, so
    collections embedded with different models can coexist.
    """
    name = model_name or DEFAULT_EMBEDDING_MODEL
    if name not in _embedders:
        _embedders[name] = TextEmbedding(name, cache_dir=EMBEDDING_CACHE_DIR)
    return _embedders[name]


def embed_documents(texts, model_name: Optional[str] = None):
    """Embeds passages/documents (no query instruction prefix)."""
    return get_embedder(model_name).embed(texts)


def embed_query(text: str, model_name: Optional[str] = None):
    """
    Embeds a single query.

    Uses the model's query embedding path when available so instruction-aware
    models such as BGE receive the required query prefix. Passages must NOT be
    embedded with this function.
    """
    embedder = get_embedder(model_name)
    query_embed = getattr(embedder, "query_embed", None)
    if callable(query_embed):
        return list(query_embed([text]))[0]
    return list(embedder.embed([text]))[0]
