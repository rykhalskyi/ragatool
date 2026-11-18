import os
import threading
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

from app.dependencies import get_message_hub, get_message_hub_instance, get_extension_manager
 # Added get_extension_manager
from app.routers import (
    items,
    collections,
    tasks,
    imports,
    mcp,
    logs,
    settings,
    files,
    extensions,
    summaries,
    auth,
    tokens,
    agent,
)
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables, get_db_connection
from contextlib import asynccontextmanager
from app.internal.auth import check_request_origin, initialize_auth, require_user
from app.internal.log_redaction import install_log_redaction
from app.internal.mcp_manager import MCPManager
from app.crud import crud_task
from app.version import APP_NAME, APP_VERSION

install_log_redaction()

# Get the singleton instance of MCPManager
mcp_manager = MCPManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    create_tables()
    initialize_auth()

    #Clear tasks if application crashed and them left in db
    db = get_db_connection()
    crud_task.delete_all_tasks(db)
    db.close()

    # Get singleton MessageHub and initialize it
    message_hub = get_message_hub_instance()
    # Start broadcaster thread for MessageHub
    threading.Thread(
        target=message_hub.broadcast_loop,
        daemon=True
    ).start()

    # Enable MCP Manager
    mcp_manager.enable()
    
    # Get ExtensionManager and ensure it's initialized and started
    # The dependency function get_extension_manager() handles DB initialization
    extension_manager = get_extension_manager() 
    # Start heartbeat if it exists and is configured
    #if hasattr(extension_manager, 'start_heartbeat') and extension_manager.heartbeat_interval_seconds > 0:
    #    extension_manager.start_heartbeat()

    yield
    
    # Shutdown: cleanup if needed
    mcp_manager.disable()
    # Shutdown ExtensionManager if it has a shutdown method
    if hasattr(extension_manager, 'shutdown'):
        extension_manager.shutdown()
    
    # MessageHub's broadcast loop is daemon, will exit with app

def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


docs_enabled = _env_flag("ENABLE_API_DOCS", False)
app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

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


@app.middleware("http")
async def enforce_origin_for_unsafe_methods(request: Request, call_next):
    """Defense-in-depth CSRF check for mutating requests."""
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        try:
            check_request_origin(request)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code, content={"detail": exc.detail}
            )
    return await call_next(request)


protected = [Depends(require_user)]

app.include_router(items.router, dependencies=protected)
app.include_router(
    collections.router,
    prefix="/collections",
    tags=["collections"],
    dependencies=protected,
)
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"], dependencies=protected)
app.include_router(
    imports.router, prefix="/import", tags=["import"], dependencies=protected
)
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"], dependencies=protected)
app.include_router(logs.router, prefix="/logs", tags=["logs"], dependencies=protected)
app.include_router(
    settings.router, prefix="/settings", tags=["settings"], dependencies=protected
)
app.include_router(files.router, prefix="/files", tags=["files"], dependencies=protected)
app.include_router(
    extensions.router, prefix="/extensions", tags=["extensions"]
)  # HTTP endpoints are protected individually; the WebSocket uses API tokens.
app.include_router(
    summaries.router, prefix="/summaries", tags=["summaries"], dependencies=protected
)
app.include_router(
    agent.router, prefix="/agent", tags=["agent"], dependencies=protected
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tokens.router, prefix="/tokens", tags=["tokens"])

@app.get("/")
def read_root():
    return {"name": APP_NAME, "version": APP_VERSION}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/version")
def read_version():
    return {"name": APP_NAME, "version": APP_VERSION}
