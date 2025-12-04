from fastapi import APIRouter, HTTPException, Depends
from app.schemas.mcp import MCPEnabledRequest
from app.internal.mcp_manager import MCPManager # Import the MCPManager class

router = APIRouter()

@router.put("/mcp_enabled")
async def set_mcp_enabled(request: MCPEnabledRequest):
    mcp_manager = MCPManager() # Get the singleton instance
    if request.enabled:
        mcp_manager.enable()
    else:
        mcp_manager.disable()
    return {"message": f"MCP server enabled status set to {request.enabled}. Current status: {mcp_manager.is_enabled()}"}
