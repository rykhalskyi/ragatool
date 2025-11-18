from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
import asyncio
from typing import List
from sqlite3 import Connection

from app.internal.message_hub import message_hub
from app.dependencies import get_db
from app.crud import crud_log
from app.schemas.mcp import Message

router = APIRouter()

@router.get("/", response_model=List[Message])
def read_logs(n: int = 50, db: Connection = Depends(get_db)):
    """
    Retrieve the latest n log entries.
    """
    return crud_log.get_latest_log_entries(db=db, n=n)

async def event_generator(request: Request):
    while True:
        # stop when client disconnects
        if await request.is_disconnected():
            break

        try:
            # block in a worker thread until a message is available
            message = await asyncio.to_thread(message_hub.get_message)

            yield f"data: {message.model_dump_json()}\n\n"

        except asyncio.CancelledError:
            break

        except Exception as e:
            # optional: log unexpected errors
            print("SSE error:", e)
            break

        # optional heartbeat
        await asyncio.sleep(0)

@router.get("/stream")
async def stream(request: Request):
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream"
    )
