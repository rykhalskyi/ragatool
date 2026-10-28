from pydantic import BaseModel, Field, model_validator
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
    chunk_overlap: int = Field(ge=0)
    no_chunks: bool

    @model_validator(mode="after")
    def _validate_chunk_overlap(self):
        if not self.no_chunks and self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self

class ChunkPreviewResponse(BaseModel):
    chunks: List[str]
    more_chunks: bool