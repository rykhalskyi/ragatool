from typing import Optional
from pydantic import BaseModel
from app.internal.chunker import ChunkType

class FileImportSettings(BaseModel):
    chunk_size: int
    chunk_overlap: int
    no_chunks: bool
    chunk_type: Optional[ChunkType] = ChunkType.DEFAULT

class UrlImportSettings(FileImportSettings):
    url: str

class Import(BaseModel):
    name: str
    model: str
    settings: FileImportSettings
