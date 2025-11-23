import pytest
from unittest.mock import Mock, patch, MagicMock
from app.internal.message_hub import MessageHub
from app.schemas.mcp import Message
from app.models.messages import MessageType
from datetime import datetime
import uuid
from app.database import get_db_connection # Added import

@pytest.fixture
def mock_crud_log():
    with patch('app.crud.crud_log.create_log') as mock:
        yield mock

@pytest.fixture
def mock_get_db_connection():
    with patch('app.database.get_db_connection') as mock: # Corrected patch target
        yield mock

@pytest.fixture
def message_hub_instance(mock_get_db_connection):
    mock_db = MagicMock() # Create a mock for the database connection
    mock_get_db_connection.return_value = mock_db # Configure the mock function get_db_connection to return this mock_db
    # Instantiate MessageHub, which will internally call the mocked get_db_connection
    message_hub = MessageHub(mock_get_db_connection())
    return message_hub

@pytest.fixture
def clear_message_hub_queue(message_hub_instance):
    # Ensure the queue is empty before each test
    while not message_hub_instance.incoming_message_queue.empty():
        message_hub_instance.incoming_message_queue.get()
    yield

def test_send_message(mock_crud_log, mock_get_db_connection, message_hub_instance, clear_message_hub_queue): # Modified test function
    test_uuid = str(uuid.uuid4())
    test_timestamp = datetime.now()
    mock_log_message = Message(
        id=test_uuid,
        timestamp=test_timestamp,
        collectionId="test-collection-id",
        collectionName="test-collection-name",
        topic="LOG",
        message="Test log message"
    )
    mock_crud_log.return_value = mock_log_message

    message_hub_instance.send_message( # Using message_hub_instance
        "test-collection-id",
        "test-collection-name",
        MessageType.LOG,
        "Test log message"
    )

    mock_get_db_connection.assert_called_once()
    mock_crud_log.assert_called_once_with(
        mock_get_db_connection.return_value,
        "test-collection-id",
        "test-collection-name",
        "LOG",
        "Test log message"
    )

    retrieved_message = message_hub_instance.incoming_message_queue.get() # Using message_hub_instance
    assert retrieved_message == mock_log_message

def test_get_message(message_hub_instance, clear_message_hub_queue): # Modified test function
    test_uuid = str(uuid.uuid4())
    test_timestamp = datetime.now()
    mock_log_message = Message(
        id=test_uuid,
        timestamp=test_timestamp,
        collectionId="test-collection-id",
        collectionName="test-collection-name",
        topic="LOG",
        message="Test log message"
    )
    message_hub_instance.incoming_message_queue.put(mock_log_message) # Using message_hub_instance

    retrieved_message = message_hub_instance.get_message() # Using message_hub_instance
    assert retrieved_message == mock_log_message
    assert message_hub_instance.incoming_message_queue.empty()
