from sqlite3 import Connection
import asyncio
import queue
import threading
import uuid
from datetime import datetime
from typing import Any, Optional, Set, Dict, Callable, Coroutine, List
from pydantic import ValidationError

from asyncio import Future
from app.internal.message_hub import MessageHub
from app.models.messages import MessageType
from app.schemas.websocket import WebSocketMessage, ClientMessage
from app.schemas.mcp import ExtensionTool, SupportedCommand
from app.schemas.mcp import ExtensionTool, SupportedCommand

import trafilatura


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
        self.messag_hub: Optional[MessageHub]= None
        self.db: Optional[Connection] = None
        self.incoming_message_queue: queue.Queue = queue.Queue()
        self.clients: Dict[str, queue.Queue] = {}
        self.client_metadata: Dict[str, ExtensionTool] = {}
        self.pending_async_requests: Dict[str, Future] = {}
        self.client_id_counter = 0
        self.heartbeat_interval_seconds: int = 60 # Default heartbeat interval
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat_event = threading.Event()
        print("INFO: ExtensionManager initialized (singleton pattern).")

    def init_with_db(self, db: Connection, mh: MessageHub):
        """Initialize with a database connection."""
        self.db = db
        self.messag_hub = mh
        print("INFO: ExtensionManager initialized with database connection.")

    def register_client(self) -> tuple[str, queue.Queue]:
        """Registers a new client and returns its ID and a queue for receiving messages."""
        client_id = str(uuid.uuid4())
        client_queue = queue.Queue()
        self.clients[client_id] = client_queue
        print(f"INFO: Client registered: {client_id}")

        notification_message = WebSocketMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            topic="extension_connected",
            message=f"Extension client {client_id} connected."
        )
        self.send_message_to_client(client_id, notification_message)

        if self.messag_hub != None:
            self.messag_hub.send_message("extension", MessageType.INFO, f"ExtensionTool connected")

        return client_id, client_queue
    
    def unregister_client(self, client_id: str):
        """Unregisters a client."""
        if client_id in self.clients:

            del self.clients[client_id]
            if client_id in self.client_metadata:
                del self.client_metadata[client_id]
            print(f"INFO: Client unregistered: {client_id}")

            if self.messag_hub != None:
                self.messag_hub.send_message("extension", MessageType.INFO, f"ExtensionTool disconnected")
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

    def get_registered_extension_tools(self) -> List[ExtensionTool]:
        """Returns a list of all currently registered extension tools."""
        return list(self.client_metadata.values())

    def process_incoming_message(self, client_id: str, message_data: Dict[str, Any]):
        """Processes a message received from a client."""
        try:
            correlation_id = message_data.get("correlation_id")
            if correlation_id and correlation_id in self.pending_async_requests:
                future = self.pending_async_requests.pop(correlation_id)
                future.get_loop().call_soon_threadsafe(future.set_result, message_data)
                print(f"INFO: Resolved async request for correlation_id: {correlation_id}")
                return

            client_message = ClientMessage(**message_data)
            print(f"INFO: Received message from client {client_id}: Type='{client_message.type}', Payload={client_message.payload}")

            if client_message.type == "command_response":
                print(f"INFO: Received command response from {client_id}. This should have a correlation_id.")

            elif client_message.type == "ping":
                try:
                    payload = client_message.payload
                    if isinstance(payload, list) and len(payload) > 0:
                        first_item = payload[0]
                        app_name = first_item.get("app")
                        entity_name = first_item.get("entityName")

                        supportedCommand = []
                        for command in payload:
                            commands_data = SupportedCommand(
                               name = command.get("name"),
                               description=command.get("description"),
                               inputSchema=command.get("input") or "no input parameters"
                            )
                           
                            supportedCommand.append(commands_data)

                        extension_tool = ExtensionTool(
                            client_id=client_id,
                            application_name=app_name,
                            user_entity_name=entity_name,
                            supported_commands=supportedCommand
                        )
                        
                        self.client_metadata[client_id] = extension_tool
                        
                except (ValidationError, TypeError, AttributeError) as e:
                    print(f"WARNING: Malformed ping payload from client {client_id}: {e}")

                response_message = WebSocketMessage(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    topic="pong",
                    message="pong"
                )
                self.send_message_to_client(client_id, response_message)
            elif client_message.type == "pong":
                print(f"INFO Pong from client {client_id}" )
            elif client_message.type == "command":
                print(f"INFO: Processing command from {client_id} with payload: {client_message.payload}")
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
            self,
        client_id: str, 
        command_name: str, 
        command_input: str, 
        timeout: int = 20
    ) -> Dict[str, str]:
        """
        Sends a command to a client and waits for a response with a correlation_id.

        Args:
            client_id: The ID of the client to send the command to.
            command_name: The command name.
            command_input: The data to send with the command.
            timeout: The time in seconds to wait for a response.

        Returns:
            The response payload from the client.

        Raises:
            TimeoutError: If the client does not respond within the timeout period.
            ConnectionError: If the client is not connected.
        """
        
        if client_id not in self.clients:
            raise ConnectionError(f"Client {client_id} is not connected or does not exist.")

        loop = asyncio.get_running_loop()
        correlation_id = str(uuid.uuid4())
        future = loop.create_future()
        
        self.pending_async_requests[correlation_id] = future

        message = WebSocketMessage(
            id=command_name,
            timestamp=datetime.now().isoformat(),
            topic="call_command",
            message= command_input,
            correlation_id=correlation_id
        )

        try:
            self.send_message_to_client(client_id, message)
            print(f"INFO: Sent command '{command_input}' to client {client_id} with correlation_id: {correlation_id}")
            
            # Wait for the future to be resolved by process_incoming_message
            response = await asyncio.wait_for(future, timeout=timeout)
            #print(f" command response: '{response}'")
            
            payload = response.get("payload", {})
            apply_filter_to = payload.get("apply_filter")
            
            if apply_filter_to != None:
                message = payload.get("message")
                content = message[0].get(apply_filter_to)
                cleaned_content = trafilatura.extract(content)
                message[0][apply_filter_to] = cleaned_content
                response["payload"]["message"] = message

            return response

        except asyncio.TimeoutError:
            # Clean up the pending request if a timeout occurs
            self.pending_async_requests.pop(correlation_id, None)
            print(f"ERROR: Timeout waiting for response from client {client_id} for correlation_id: {correlation_id}")
            raise TimeoutError(f"Client {client_id} did not respond within {timeout} seconds.")
        except Exception as e:
            self.pending_async_requests.pop(correlation_id, None)
            print(f"ERROR: An error occurred while sending command and waiting for response: {e}")
            raise