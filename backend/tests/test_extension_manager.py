import unittest
from unittest.mock import MagicMock, patch, ANY
import queue
import time
import uuid
from datetime import datetime
from app.internal.extension_manager import ExtensionManager
from app.schemas.websocket import WebSocketMessage, ClientMessage

class TestExtensionManager(unittest.TestCase):

    def setUp(self):
        # Reset the singleton instance before each test
        ExtensionManager._instance = None
        self.manager = ExtensionManager()
        self.mock_db = MagicMock()
        self.mock_mh = MagicMock()
        self.manager.init_with_db(self.mock_db, self.mock_mh)

    def tearDown(self):
        # Clean up by shutting down the manager
        self.manager.shutdown()
        ExtensionManager._instance = None

    def test_singleton_pattern(self):
        """Test that ExtensionManager implements the singleton pattern correctly."""
        instance1 = ExtensionManager()
        instance2 = ExtensionManager()
        self.assertIs(instance1, instance2)

    def test_init_with_db(self):
        """Test that the database connection is initialized."""
        self.assertIsNotNone(self.manager.db)
        self.assertEqual(self.manager.db, self.mock_db)

    def test_register_and_unregister_client(self):
        """Test client registration and unregistration."""
        client_id, client_queue = self.manager.register_client()
        self.assertIn(client_id, self.manager.clients)
        self.assertIsInstance(client_queue, queue.Queue)

        self.manager.unregister_client(client_id)
        self.assertNotIn(client_id, self.manager.clients)

    def test_send_message_to_client(self):
        """Test sending a message to a specific client."""
        client_id, client_queue = self.manager.register_client()
        message = WebSocketMessage(id=str(uuid.uuid4()), timestamp=datetime.now().isoformat(), topic="test", message="Hello")
        
        self.manager.send_message_to_client(client_id, message)
        
        try:
            received_message = client_queue.get(timeout=1)
            self.assertEqual(received_message, message)
        except queue.Empty:
            self.fail("Message was not received by the client.")

    def test_broadcast_message(self):
        """Test broadcasting a message to all clients."""
        client_id1, queue1 = self.manager.register_client()
        client_id2, queue2 = self.manager.register_client()
        
        message = WebSocketMessage(id=str(uuid.uuid4()), timestamp=datetime.now().isoformat(), topic="broadcast", message="Everyone")

        self.manager.broadcast_message(message)

        try:
            msg1 = queue1.get(timeout=1)
            msg2 = queue2.get(timeout=1)
            self.assertEqual(msg1, message)
            self.assertEqual(msg2, message)
        except queue.Empty:
            self.fail("Broadcast message was not received by all clients.")

    def test_process_incoming_ping(self):
        """Test processing a 'ping' message from a client."""
        client_id, client_queue = self.manager.register_client()
        ping_message_data = {"type": "ping", "payload": []}

        self.manager.process_incoming_message(client_id, ping_message_data)

        try:
            response = client_queue.get(timeout=1)
            self.assertEqual(response.topic, "pong")
        except queue.Empty:
            self.fail("Did not receive pong response.")
            
    def test_process_incoming_ping_with_metadata(self):
        """Test processing a 'ping' message with metadata."""
        client_id, client_queue = self.manager.register_client()
        metadata = {
            "name": "Test App",
            "description": "A test extension",
            "inputSchema": {},
            "app": "test_app",
            "entityName": "Tester"
        }
        ping_message_data = {"type": "ping", "payload": [metadata]}

        self.manager.process_incoming_message(client_id, ping_message_data)
        
        self.assertIn(client_id, self.manager.client_metadata)
        self.assertEqual(self.manager.client_metadata[client_id].application_name, "test_app")

    def test_process_unknown_message_type(self):
        """Test processing a message with an unknown type."""
        client_id, client_queue = self.manager.register_client()
        unknown_message_data = {"type": "unknown_type", "payload": {}}

        self.manager.process_incoming_message(client_id, unknown_message_data)

        try:
            response = client_queue.get(timeout=1)
            self.assertEqual(response.topic, "error")
            self.assertIn("Unknown command type", response.message)
        except queue.Empty:
            self.fail("Did not receive error response for unknown message type.")

    def test_process_malformed_message(self):
        """Test processing a malformed message."""
        client_id, client_queue = self.manager.register_client()
        malformed_message_data = {"foo": "bar"} # Missing 'type' field

        self.manager.process_incoming_message(client_id, malformed_message_data)
        
        try:
            response = client_queue.get(timeout=1)
            self.assertEqual(response.topic, "error")
            self.assertIn("Server error processing message", response.message)
        except queue.Empty:
            self.fail("Did not receive error response for malformed message.")

    @patch('threading.Thread')
    def test_start_and_stop_heartbeat(self, mock_thread_class):
        """Test the start and stop of the heartbeat thread."""
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance

        # Start heartbeat
        self.manager.heartbeat_interval_seconds = 1
        self.manager.start_heartbeat()
        mock_thread_class.assert_called_once_with(target=self.manager._run_heartbeat, daemon=True)
        mock_thread_instance.start.assert_called_once()
        self.assertIsNotNone(self.manager._heartbeat_thread)

        # Stop heartbeat
        self.manager.stop_heartbeat()
        self.assertTrue(self.manager._stop_heartbeat_event.is_set())
        mock_thread_instance.join.assert_called_once()
        self.assertIsNone(self.manager._heartbeat_thread)

    def test_shutdown(self):
        """Test the shutdown process."""
        client_id, _ = self.manager.register_client()
        self.assertIn(client_id, self.manager.clients)

        with patch.object(self.manager, 'stop_heartbeat') as mock_stop_heartbeat:
            self.manager.shutdown()
            mock_stop_heartbeat.assert_called_once()

        self.assertEqual(len(self.manager.clients), 0)


    def test_send_command_and_wait_for_response(self):
        """Test the async request-reply pattern successfully returns a response."""
        import asyncio
        import threading
        
        client_id, client_queue = self.manager.register_client()
        
        def client_simulator():
            try:
                # 1. Client waits for the command from the manager
                command_message: WebSocketMessage = client_queue.get(timeout=2)
                
                self.assertEqual(command_message.topic, "call_command")
                self.assertIsNotNone(command_message.correlation_id)
                
                # 2. Client processes and sends a response
                response_payload = {
                    "status": "completed",
                    "result": "here is your data",
                    "correlation_id": command_message.correlation_id
                }
                self.manager.process_incoming_message(client_id, response_payload)
            except queue.Empty:
                self.fail("Client simulator did not receive a message.")

        # Run the client simulator in a separate thread
        client_thread = threading.Thread(target=client_simulator)
        client_thread.start()

        async def run_test():
            # 3. Main thread sends a command and awaits the response
            response = await self.manager.send_command_and_wait_for_response(
                client_id=client_id,
                command_name="test_command",
                command_input='{"data": "some_input"}', # Changed to string
                timeout=5
            )
            # 4. Assert the response is what the client sent
            self.assertEqual(response["status"], "completed")
            self.assertEqual(response["result"], "here is your data")

        # Run the async test
        asyncio.run(run_test())
        client_thread.join()

    def test_send_command_and_wait_for_response_timeout(self):
        """Test that the async request-reply pattern raises a TimeoutError."""
        import asyncio

        client_id, client_queue = self.manager.register_client()

        async def run_test():
            # We expect a TimeoutError because the client will not send a response
            with self.assertRaises(TimeoutError):
                await self.manager.send_command_and_wait_for_response(
                    client_id=client_id,
                    command_name="test_command",
                    command_input='{"data": "some_input"}', # Changed to string
                    timeout=0.1  # Use a short timeout
                )
            
            # Ensure the pending request is cleaned up after timeout
            self.assertEqual(len(self.manager.pending_async_requests), 0)

        # Run the async test
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
