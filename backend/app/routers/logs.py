from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
import asyncio

from app.internal.message_hub import message_hub

router = APIRouter()

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
