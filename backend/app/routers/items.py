from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.crud.crud_collection import get_enabled_collections_for_mcp
from app.database import get_db_connection
from app.internal.retrieval import retrieve

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
        return retrieve(collection_id, payload.query, n_results=payload.n_results)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Collection '{collection_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
