import pytest
from unittest.mock import Mock, patch
from app.internal.message_hub import MessageHub, message_hub
from app.schemas.mcp import Message
from datetime import datetime
import uuid

@pytest.fixture
def mock_crud_log():
    with patch('app.crud.crud_log.create_log') as mock:
        yield mock

@pytest.fixture
def mock_get_db_connection():
    with patch('app.internal.message_hub.get_db_connection') as mock:
        yield mock

@pytest.fixture
def clear_message_hub_queue():
    # Ensure the queue is empty before each test
    while not message_hub.message_queue.empty():
        message_hub.message_queue.get()
    yield

def test_send_message(mock_crud_log, mock_get_db_connection, clear_message_hub_queue):
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

    message_hub.send_message(
        "test-collection-id",
        "test-collection-name",
        "LOG",
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
    mock_get_db_connection.return_value.close.assert_called_once()

    retrieved_message = message_hub.message_queue.get()
    assert retrieved_message == mock_log_message

def test_get_message(clear_message_hub_queue):
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
    message_hub.message_queue.put(mock_log_message)

    retrieved_message = message_hub.get_message()
    assert retrieved_message == mock_log_message
    assert message_hub.message_queue.empty()
