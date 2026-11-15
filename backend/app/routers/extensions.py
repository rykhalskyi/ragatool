from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime
import uuid
import asyncio
import queue # Import queue for type hinting
from functools import partial

from app.crud import crud_token
from app.database import db_session
from app.internal.auth import TOKEN_PREFIX, hash_token, require_user
from app.internal.extension_manager import ExtensionManager
from app.dependencies import get_extension_manager
from app.schemas.websocket import WebSocketMessage, ClientMessage
from app.schemas.mcp import ExtensionTool, CallToolRequest, CallToolResponse

router = APIRouter()


WS_SUBPROTOCOL = "ragatool"


def _offered_subprotocols(websocket: WebSocket) -> list[str]:
    raw = websocket.headers.get("sec-websocket-protocol", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _extract_ws_credentials(websocket: WebSocket) -> tuple[str | None, str | None]:
    """Return (api_token, subprotocol_to_accept).

    The token may come from an Authorization header (native clients) or from a
    WebSocket subprotocol offer (browser clients). It is never accepted from the
    query string, where it would end up in access logs.
    """
    authorization = websocket.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        if token.startswith(TOKEN_PREFIX):
            return token, None

    offered = _offered_subprotocols(websocket)
    if WS_SUBPROTOCOL in offered:
        for protocol in offered:
            if protocol != WS_SUBPROTOCOL and protocol.startswith(TOKEN_PREFIX):
                return protocol, WS_SUBPROTOCOL
    return None, None


def _is_valid_ws_token(token: str | None) -> bool:
    if not token or not token.startswith(TOKEN_PREFIX):
        return False
    with db_session() as db:
        row = crud_token.find_active_by_hash(db, hash_token(token))
        if row is None:
            return False
        crud_token.touch_token(db, row["id"])
    return True

async def send_messages_to_client(websocket: WebSocket, client_id: str, client_queue: queue.Queue, extension_manager: ExtensionManager):
    """
    Task to read messages from the client's queue and send them via WebSocket.
    """
    loop = asyncio.get_running_loop()
    while True:
        try:
            # Get message from queue. This will block if the queue is empty.
            # Use a timeout to allow checking for disconnection periodically.
            message: WebSocketMessage = await loop.run_in_executor(None, partial(client_queue.get, timeout=1.0))
            # Ensure message is serializable, model_dump() is for Pydantic v2
            await websocket.send_json(message.model_dump()) 
        except queue.Empty:
            # Queue is empty, continue loop to check for new messages or disconnection
            continue
        except WebSocketDisconnect:
            # If WebSocket disconnects while trying to send, stop this task
            print(f"INFO: Send task for {client_id} stopping due to WebSocketDisconnect.")
            break
        except Exception as e:
            print(f"ERROR: Error sending message to client {client_id}: {e}")
            # Unregister client if sending fails critically
            extension_manager.unregister_client(client_id)
            break

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    extension_manager: ExtensionManager = Depends(get_extension_manager)
):
    print("INFO: WebSocket connection requested.")
    token, subprotocol = _extract_ws_credentials(websocket)
    if not _is_valid_ws_token(token):
        print("WARNING: Rejecting extension WebSocket with a missing or invalid token.")
        await websocket.close(code=1008)
        return

    await websocket.accept(subprotocol=subprotocol)
    client_id, client_queue = extension_manager.register_client()
    print(f"INFO: WebSocket accepted connection for client: {client_id}")
    
    # Start a background task to send messages from the queue to the client
    sender_task = asyncio.create_task(send_messages_to_client(websocket, client_id, client_queue, extension_manager))

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            extension_manager.process_incoming_message(client_id, data)
            
    except WebSocketDisconnect:
        print(f"INFO: Client disconnected: {client_id}")
        # The sender_task will likely exit on WebSocketDisconnect as well
    except Exception as e:
        print(f"ERROR: An error occurred with client {client_id}: {e}")
        # Log the error and ensure the client is unregistered
        extension_manager.unregister_client(client_id)
    finally:
        print(f"INFO: Cleaning up client {client_id}")
        # Ensure sender task is cancelled and client is unregistered
        sender_task.cancel()
        try:
            await sender_task
        except asyncio.CancelledError:
            pass # Expected when task is cancelled
        extension_manager.unregister_client(client_id)

@router.get("/connected_tools", response_model=List[ExtensionTool])
def get_connected_extension_tools(
    extension_manager: ExtensionManager = Depends(get_extension_manager),
    _user: dict = Depends(require_user),
):
    """
    Returns a list of all currently registered and connected extension tools.
    """
    return extension_manager.get_registered_extension_tools()

@router.post("/call_tool", response_model=CallToolResponse)
async def call_extension_tool(
    request: CallToolRequest,
    extension_manager: ExtensionManager = Depends(get_extension_manager),
    _user: dict = Depends(require_user),
):
    """
    Calls a command on a connected extension tool.
    """
    try:
        response = await extension_manager.send_command_and_wait_for_response(
            request.extension_id, 
            request.command_name, 
            request.arguments, 
            timeout=20
        )
        return CallToolResponse(
            status="success",
            result=response.get("payload")
        )
    except ConnectionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=408, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
