from typing import Optional

import chromadb

from app.internal.embedding_manager import DEFAULT_EMBEDDING_MODEL

CHROMA_PATH = "./chroma_data"
VECTOR_SPACE = "cosine"
EMBEDDING_MODEL_METADATA_KEY = "embedding_model"


def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection(name: str, client: Optional[chromadb.PersistentClient] = None):
    client = client or get_client()
    return client.get_collection(name=name)


def get_or_create_collection(
    name: str,
    embedding_model: Optional[str] = None,
    client: Optional[chromadb.PersistentClient] = None,
):
    """
    Creates a collection with the cosine distance metric.

    Chroma's default metric is L2; explicitly setting cosine keeps distances
    consistent across every code path that creates collections.
    """
    client = client or get_client()
    metadata = {"hnsw:space": VECTOR_SPACE}
    if embedding_model:
        metadata[EMBEDDING_MODEL_METADATA_KEY] = embedding_model
    return client.get_or_create_collection(name=name, metadata=metadata)


def get_collection_embedding_model(collection) -> str:
    """
    Returns the embedding model stored for a collection.

    Collections created before model metadata existed are assumed to use the
    current default model; such collections must be re-imported if they were
    embedded with an older model.
    """
    metadata = getattr(collection, "metadata", None) or {}
    return metadata.get(EMBEDDING_MODEL_METADATA_KEY) or DEFAULT_EMBEDDING_MODEL
