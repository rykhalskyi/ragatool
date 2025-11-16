import os
from fastapi import FastAPI
from app.routers import items, poc, collections, tasks, imports, mcp
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from contextlib import asynccontextmanager
from app.internal.mcp_manager import MCPManager

# Get the singleton instance of MCPManager
mcp_manager = MCPManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    create_tables()
   
    mcp_manager.enable()
    
    yield
    
    # Shutdown: cleanup if needed
    mcp_manager.disable()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
)

app.include_router(poc.router)
app.include_router(items.router)
app.include_router(collections.router, prefix="/collections", tags=["collections"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(imports.router, prefix="/import", tags=["import"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
