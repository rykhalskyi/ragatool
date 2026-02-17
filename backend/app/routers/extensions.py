from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Any, List
from datetime import datetime
import uuid
import asyncio
import queue # Import queue for type hinting
from functools import partial

from app.internal.extension_manager import ExtensionManager
from app.dependencies import get_extension_manager
from app.schemas.websocket import WebSocketMessage, ClientMessage
from app.schemas.mcp import ExtensionTool

router = APIRouter()

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
    await websocket.accept()
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
    extension_manager: ExtensionManager = Depends(get_extension_manager)
):
    """
    Returns a list of all currently registered and connected extension tools.
    """
    return extension_manager.get_registered_extension_tools()
