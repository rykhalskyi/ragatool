import pytest
import sqlite3
from unittest.mock import Mock, patch
from app.crud.crud_log import create_log
from app.schemas.mcp import Message
import uuid
from datetime import datetime

@pytest.fixture
def mock_db_connection():
    conn = Mock(spec=sqlite3.Connection)
    conn.cursor.return_value = Mock(spec=sqlite3.Cursor)
    return conn

def test_create_log(mock_db_connection):
    test_uuid = str(uuid.uuid4())
    test_timestamp = datetime.now().isoformat()
    
    with patch('uuid.uuid4', return_value=uuid.UUID(test_uuid)):
        # Mock the cursor's fetchone to return a dictionary-like object
        mock_db_connection.cursor.return_value.fetchone.return_value = {
            "id": test_uuid,
            "timestamp": test_timestamp,
            "collectionId": "test-collection-id",
            "collectionName": "test-collection-name",
            "topic": "LOG",
            "message": "Test log message"
        }

        log_message = create_log(
            mock_db_connection,
            "test-collection-id",
            "test-collection-name",
            "LOG",
            "Test log message"
        )

        mock_db_connection.cursor.assert_called_once()
        mock_db_connection.cursor.return_value.execute.assert_any_call(
            "INSERT INTO logs (id, collectionId, collectionName, topic, message) VALUES (?, ?, ?, ?, ?)",
            (
                test_uuid, # Use test_uuid here
                "test-collection-id",
                "test-collection-name",
                "LOG",
                "Test log message"
            ),
        )
        mock_db_connection.commit.assert_called_once()
        mock_db_connection.cursor.return_value.execute.assert_any_call(
            "SELECT id, timestamp, collectionId, collectionName, topic, message FROM logs WHERE id = ?",
            (test_uuid,), # Use test_uuid here
        )

        assert isinstance(log_message, Message)
        assert log_message.id == test_uuid
        assert log_message.collectionId == "test-collection-id"
        assert log_message.collectionName == "test-collection-name"
        assert log_message.topic == "LOG"
        assert log_message.message == "Test log message"
