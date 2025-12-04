from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MCPEnabledRequest(BaseModel):
    enabled: bool

class Message(BaseModel):
    id: str
    timestamp: datetime
    collectionId: Optional[str] = None
    topic: str
    message: str
