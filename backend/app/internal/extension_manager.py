from sqlite3 import Connection
import asyncio
import queue
import threading
import uuid
from datetime import datetime
from typing import Any, Optional, Set, Dict, Callable, Coroutine

from asyncio import Future
from app.schemas.websocket import WebSocketMessage, ClientMessage # Import actual Pydantic models

class ExtensionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.db: Optional[Connection] = None
        self.incoming_message_queue: queue.Queue = queue.Queue()
        self.clients: Dict[str, queue.Queue] = {}
        self.client_metadata: Dict[str, Dict] = {}
        self.pending_async_requests: Dict[str, Future] = {}
        self.client_id_counter = 0
        self.heartbeat_interval_seconds: int = 60 # Default heartbeat interval
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat_event = threading.Event()
        print("INFO: ExtensionManager initialized (singleton pattern).")

    def init_with_db(self, db: Connection):
        """Initialize with a database connection."""
        self.db = db
        print("INFO: ExtensionManager initialized with database connection.")

    def register_client(self) -> tuple[str, queue.Queue]:
        """Registers a new client and returns its ID and a queue for receiving messages."""
        client_id = str(uuid.uuid4())
        client_queue = queue.Queue()
        self.clients[client_id] = client_queue
        print(f"INFO: Client registered: {client_id}")
        return client_id, client_queue
    
    def unregister_client(self, client_id: str):
        """Unregisters a client."""
        if client_id in self.clients:
            del self.clients[client_id]
            if client_id in self.client_metadata:
                del self.client_metadata[client_id]
            print(f"INFO: Client unregistered: {client_id}")
        else:
            print(f"WARNING: Attempted to unregister non-existent client: {client_id}")

    def broadcast_message(self, message: WebSocketMessage):
        """Sends a message to all connected clients."""
        print(f"INFO: Broadcasting message: {message.topic} - {message.message}")
        for client_id, client_queue in list(self.clients.items()):
            try:
                if isinstance(message, WebSocketMessage):
                    client_queue.put(message)
                else:
                    print(f"ERROR: broadcast_message received non-WebSocketMessage type for client {client_id}")
            except Exception as e:
                print(f"ERROR: Error sending broadcast to client {client_id}: {e}")
                self.unregister_client(client_id)

    def send_message_to_client(self, client_id: str, message: WebSocketMessage):
        """Sends a message to a specific client."""
        if client_id in self.clients:
            client_queue = self.clients[client_id]
            try:
                if isinstance(message, WebSocketMessage):
                    client_queue.put(message)
                    print(f"INFO: Message sent to client {client_id}: {message.topic} - {message.message}")
                else:
                    print(f"ERROR: send_message_to_client received non-WebSocketMessage type for client {client_id}")
            except Exception as e:
                print(f"ERROR: Error sending message to client {client_id}: {e}")
                self.unregister_client(client_id)
        else:
            print(f"WARNING: Client {client_id} not found, cannot send message.")

    def process_incoming_message(self, client_id: str, message_data: Dict[str, Any]):
        """Processes a message received from a client."""
        try:
            # Check if it's a response to a pending async request
            correlation_id = message_data.get("correlation_id")
            if correlation_id and correlation_id in self.pending_async_requests:
                future = self.pending_async_requests.pop(correlation_id)
                # Resolve the future in a thread-safe way
                future.get_loop().call_soon_threadsafe(future.set_result, message_data)
                print(f"INFO: Resolved async request for correlation_id: {correlation_id}")
                return

            client_message = ClientMessage(**message_data) 
            print(f"INFO: Received message from client {client_id}: Type='{client_message.type}', Payload={client_message.payload}")
            
            if client_message.type == "command_response":
                print(f"INFO: Received command response from {client_id}. This should have a correlation_id.")
                # This case is now handled by the correlation_id check at the beginning
                pass

            elif client_message.type == "ping":
                if client_message.payload and isinstance(client_message.payload, list) and len(client_message.payload) > 0:
                    first_item = client_message.payload[0]
                    if isinstance(first_item, dict) and "app" in first_item and "entityName" in first_item:
                        metadata = {
                            "name": first_item.get("name"),
                            "description": first_item.get("description"),
                            "inputScheme": first_item.get("inputSchema"),
                            "app": first_item.get("app"),
                            "entityName": first_item.get("entityName")
                        }
                        self.client_metadata[client_id] = metadata
                        print(f"INFO: Updated metadata for client {client_id}: {metadata}")
                response_message = WebSocketMessage(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    topic="pong",
                    message="pong"
                )
                self.send_message_to_client(client_id, response_message)
            elif client_message.type == "command":
                print(f"INFO: Processing command from {client_id} with payload: {client_message.payload}")
                # TODO: Implement command processing logic here.
                pass
            else:
                print(f"WARNING: Unknown message type from client {client_id}: {client_message.type}")
                error_response = WebSocketMessage(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    topic="error",
                    message=f"Unknown command type: {client_message.type}"
                )
                self.send_message_to_client(client_id, error_response)
                
        except Exception as e:
            print(f"ERROR: Error processing incoming message from client {client_id}: {e}")
            error_response = WebSocketMessage(
                id=str(uuid.uuid4()),
                timestamp=datetime.now().isoformat(),
                topic="error",
                message=f"Server error processing message: {e}"
            )
            # Avoid sending an error response if the client is gone
            if client_id in self.clients:
                self.send_message_to_client(client_id, error_response)


    def _run_heartbeat(self):
        """Periodically checks if clients are still alive. Placeholder implementation."""
        print("INFO: Heartbeat thread started.")
        while not self._stop_heartbeat_event.is_set():
            self._stop_heartbeat_event.wait(self.heartbeat_interval_seconds)
            if self._stop_heartbeat_event.is_set():
                break

            print("DEBUG: Running heartbeat check...")
            ping_message = WebSocketMessage(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    topic="ping",
                    message="ping")
            
            self.broadcast_message(ping_message)
            # Placeholder for actual heartbeat logic
            pass
        print("INFO: Heartbeat thread stopped.")

    def start_heartbeat(self):
        """Starts the heartbeat monitoring thread if it's not already running."""
        if self.heartbeat_interval_seconds > 0 and (self._heartbeat_thread is None or not self._heartbeat_thread.is_alive()):
            self._stop_heartbeat_event.clear()
            self._heartbeat_thread = threading.Thread(
                target=self._run_heartbeat,
                daemon=True
            )
            self._heartbeat_thread.start()
            print("INFO: Heartbeat monitoring started.")
        elif self.heartbeat_interval_seconds <= 0:
            print("INFO: Heartbeat is disabled (interval <= 0).")
        else:
            print("INFO: Heartbeat thread already running.")


    def stop_heartbeat(self):
        """Stops the heartbeat monitoring thread."""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._stop_heartbeat_event.set()
            self._heartbeat_thread.join() 
            self._heartbeat_thread = None
            print("INFO: Heartbeat monitoring stopped.")

    def shutdown(self):
        """Cleans up resources when the manager is shut down."""
        print("INFO: Shutting down ExtensionManager...")
        self.stop_heartbeat()
        for client_id in list(self.clients.keys()):
            self.unregister_client(client_id)
        if self.db:
            pass 
        print("INFO: ExtensionManager shut down complete.")


async def send_command_and_wait_for_response(
    client_id: str, 
    command: str, 
    payload: Any, 
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Sends a command to a client and waits for a response with a correlation_id.

    Args:
        client_id: The ID of the client to send the command to.
        command: The command topic/name.
        payload: The data to send with the command.
        timeout: The time in seconds to wait for a response.

    Returns:
        The response payload from the client.

    Raises:
        TimeoutError: If the client does not respond within the timeout period.
        ConnectionError: If the client is not connected.
    """
    manager = ExtensionManager()
    if client_id not in manager.clients:
        raise ConnectionError(f"Client {client_id} is not connected or does not exist.")

    loop = asyncio.get_running_loop()
    correlation_id = str(uuid.uuid4())
    future = loop.create_future()
    
    manager.pending_async_requests[correlation_id] = future

    message = WebSocketMessage(
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        topic=command,
        message="command",
        payload=payload,
        correlation_id=correlation_id
    )

    try:
        manager.send_message_to_client(client_id, message)
        print(f"INFO: Sent command '{command}' to client {client_id} with correlation_id: {correlation_id}")
        
        # Wait for the future to be resolved by process_incoming_message
        response = await asyncio.wait_for(future, timeout=timeout)
        return response

    except asyncio.TimeoutError:
        # Clean up the pending request if a timeout occurs
        manager.pending_async_requests.pop(correlation_id, None)
        print(f"ERROR: Timeout waiting for response from client {client_id} for correlation_id: {correlation_id}")
        raise TimeoutError(f"Client {client_id} did not respond within {timeout} seconds.")
    except Exception as e:
        manager.pending_async_requests.pop(correlation_id, None)
        print(f"ERROR: An error occurred while sending command and waiting for response: {e}")
        raise