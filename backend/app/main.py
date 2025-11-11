from fastapi import FastAPI
from app.routers import items, poc, collections, tasks
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    create_tables()
    yield
    # Shutdown: cleanup if needed
    pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(poc.router)
app.include_router(items.router)
app.include_router(collections.router, prefix="/collections", tags=["collections"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
