from pydantic import BaseModel, Field
from typing import List

from app.internal.chunker import ChunkType

class File(BaseModel):
    id: str
    timestamp: str
    collection_id: str
    path: str
    source: str

class ChunkPreviewRequest(BaseModel):
    file_id: str
    skip_number: int = 0
    take_number: int = 10
    chunk_type: ChunkType
    chunk_size: int = Field(gt=0)
    chunk_overlap: int
    no_chunks: bool

class ChunkPreviewResponse(BaseModel):
    chunks: List[str]
    more_chunks: bool