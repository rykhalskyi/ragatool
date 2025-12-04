import pytest
import sqlite3
from unittest.mock import Mock, patch
from app.crud.crud_log import create_log, get_latest_log_entries
from app.schemas.mcp import Message
import uuid
from datetime import datetime, timedelta

@pytest.fixture
def mock_db_connection():
    conn = Mock(spec=sqlite3.Connection)
    conn.cursor.return_value = Mock(spec=sqlite3.Cursor)
    return conn

@pytest.fixture
def in_memory_db():
    conn = sqlite3.connect(":memory:")
    from app.database import create_tables
    create_tables(conn)
    yield conn
    conn.close()

def test_create_log(mock_db_connection):
    test_uuid = uuid.uuid4()
    with patch('uuid.uuid4', return_value=test_uuid):
        log_message = create_log(
            mock_db_connection,
            "test-collection-id",
            "LOG",
            "Test log message"
        )
        mock_db_connection.cursor.return_value.execute.assert_any_call(
            "INSERT INTO logs (id, collectionId, topic, message) VALUES (?, ?, ?, ?)",
            (
                str(test_uuid),
                "test-collection-id",
                "LOG",
                "Test log message"
            ),
        )
        mock_db_connection.commit.assert_called_once()
        assert isinstance(log_message, Message)
        assert log_message.id == str(test_uuid)
        assert log_message.collectionId == "test-collection-id"
        assert log_message.topic == "LOG"
        assert log_message.message == "Test log message"
        assert isinstance(log_message.timestamp, datetime)

def test_get_latest_log_entries(in_memory_db):
    # Insert some log entries
    now = datetime.now()
    log_entries_data = [
        {"id": str(uuid.uuid4()), "timestamp": (now - timedelta(seconds=3)).isoformat(), "collectionId": "c1", "topic": "T1", "message": "M1"},
        {"id": str(uuid.uuid4()), "timestamp": (now - timedelta(seconds=2)).isoformat(), "collectionId": "c2", "topic": "T2", "message": "M2"},
        {"id": str(uuid.uuid4()), "timestamp": (now - timedelta(seconds=1)).isoformat(), "collectionId": "c3", "topic": "T3", "message": "M3"},
        {"id": str(uuid.uuid4()), "timestamp": now.isoformat(), "collectionId": "c4", "topic": "T4", "message": "M4"},
    ]

    cursor = in_memory_db.cursor()
    for entry in log_entries_data:
        cursor.execute(
            "INSERT INTO logs (id, timestamp, collectionId, topic, message) VALUES (?, ?, ?, ?, ?)",
            (entry["id"], entry["timestamp"], entry["collectionId"], entry["topic"], entry["message"]),
        )
    in_memory_db.commit()

    # Test getting the latest 2 entries
    latest_2_entries = get_latest_log_entries(in_memory_db, 2)
    assert len(latest_2_entries) == 2
    assert latest_2_entries[0].message == "M4"
    assert latest_2_entries[1].message == "M3"

    # Test getting all entries
    all_entries = get_latest_log_entries(in_memory_db, 10)
    assert len(all_entries) == 4
    assert all_entries[0].message == "M4"
    assert all_entries[1].message == "M3"
    assert all_entries[2].message == "M2"
    assert all_entries[3].message == "M1"

    # Test getting 0 entries
    no_entries = get_latest_log_entries(in_memory_db, 0)
    assert len(no_entries) == 0
