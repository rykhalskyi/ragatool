from typing import Optional, List
from pydantic import BaseModel, Field, Json, model_validator
from app.internal.chunker import ChunkType

class FileImportSettings(BaseModel):
    chunk_size: int = Field(gt=0)
    chunk_overlap: int = Field(ge=0)
    no_chunks: bool
    chunk_type: Optional[ChunkType] = ChunkType.DEFAULT
    filter: Optional[str] = None

    @model_validator(mode="after")
    def _validate_chunk_overlap(self):
        if not self.no_chunks and self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self

class UrlImportSettings(FileImportSettings):
    url: str

class Import(BaseModel):
    name: str
    model: str
    settings: FileImportSettings

class ImportFileStep2In(BaseModel):
    import_files_ids: Json[List[str]]
    import_params: str
