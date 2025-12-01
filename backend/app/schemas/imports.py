from pydantic import BaseModel

class FileImportSettings(BaseModel):
    chunk_size: int
    chunk_overlap: int
    no_chunks: bool

class UrlImportSettings(FileImportSettings):
    url: str

class Import(BaseModel):
    name: str
    model: str
    settings: FileImportSettings
