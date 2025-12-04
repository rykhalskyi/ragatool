from pydantic import BaseModel

class Task(BaseModel):
    id: str
    collectionId: str
    name: str
    startTime: int
    status: str
