from pydantic import BaseModel

class MCPEnabledRequest(BaseModel):
    enabled: bool
