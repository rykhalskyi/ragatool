import os
import threading
from fastapi import FastAPI
from app.dependencies import get_message_hub, get_message_hub_instance
from app.routers import items, collections, tasks, imports, mcp, logs, settings
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables, get_db_connection
from contextlib import asynccontextmanager
from app.internal.mcp_manager import MCPManager
from app.crud import crud_task

# Get the singleton instance of MCPManager
mcp_manager = MCPManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    create_tables()
   
    #Clear tasks if application crashed and them left in db
    db = get_db_connection()
    crud_task.delete_all_tasks(db)
    db.close()

        # Get singleton MessageHub
    message_hub = get_message_hub_instance()

    # Start broadcaster thread
    threading.Thread(
        target=message_hub.broadcast_loop,
        daemon=True
    ).start()

    mcp_manager.enable()
    
    yield
    
    # Shutdown: cleanup if needed
    mcp_manager.disable()

app = FastAPI(lifespan=lifespan)

# Read allowed origins from environment variable, or use default for local development
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
)

app.include_router(items.router)
app.include_router(collections.router, prefix="/collections", tags=["collections"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(imports.router, prefix="/import", tags=["import"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
