from fastapi import FastAPI
from app.routers import items, users

app = FastAPI()

app.include_router(users.router)
app.include_router(items.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
