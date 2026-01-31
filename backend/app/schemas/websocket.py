from pydantic import BaseModel, ConfigDict
from typing import Any, Optional

class WebSocketMessage(BaseModel):
    id: str # Unique message ID
    timestamp: str
    topic: str # e.g., "status", "notification", "data"
    message: Optional[str] # Payload
    collectionId: Optional[str] = None # Optional: context from a specific collection
    correlation_id: Optional[str] = None # Added for request-reply pattern

class ClientMessage(BaseModel):
    type: str # e.g., "command", "ping", "status_update"
    payload: Any # Message content/command arguments
