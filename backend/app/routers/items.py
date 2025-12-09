import chromadb
from fastapi import APIRouter, HTTPException
from fastembed import TextEmbedding
import numpy as np
from pydantic import BaseModel

from app.crud.crud_collection import get_enabled_collections_for_mcp
from app.database import get_db_connection

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    n_results: int = 10


@router.get("/items/")
def read_items():
    with get_db_connection() as db:
        collections = get_enabled_collections_for_mcp(db)
        return collections


@router.post("/query/{collection_id}")
def query_database(collection_id: str, payload: QueryRequest):
    try:
        client = chromadb.PersistentClient(path="./chroma_data")
        collection = client.get_collection(name=collection_id)
        embedder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

        query_emb = np.array(list(embedder.embed([payload.query])))


        results = collection.query(query_embeddings=query_emb.tolist(), n_results=payload.n_results)
        return {"status": "success", "results": results}
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Collection '{collection_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Normalization if needed
#def normalize(arr):
#        return arr / np.linalg.norm(arr, axis=1, keepdims=True)