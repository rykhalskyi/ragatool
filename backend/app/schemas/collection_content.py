from pydantic import BaseModel
from typing import List, Any

class CollectionContentRequest(BaseModel):
    page: int = 1
    page_size: int = 10

class CollectionContentResponse(BaseModel):
    chunks: List[Any]
    total_chunks: int
    page: int
    page_size: int

class CollectionQueryResponse(BaseModel):
    status: str
    results: Any
