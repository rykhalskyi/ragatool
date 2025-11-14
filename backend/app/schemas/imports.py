from pydantic import BaseModel

class Import(BaseModel):
    name: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
