from pydantic import BaseModel

class File(BaseModel):
    id: str
    timestamp: str
    collection_id: str
    path: str
    source: str