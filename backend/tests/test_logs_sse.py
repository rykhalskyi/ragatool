import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.schemas.mcp import Message
from datetime import datetime
import asyncio

client = TestClient(app)

@pytest.fixture
def mock_asyncio_to_thread():
    with patch('app.routers.logs.asyncio.to_thread') as mock:
        yield mock

@pytest.mark.asyncio
async def test_sse_stream(mock_asyncio_to_thread):
    test_message_1 = Message(
        id="test-uuid-1",
        timestamp=datetime.now(),
        collectionId="col1",
        collectionName="Collection 1",
        topic="LOG",
        message="Test log message 1"
    )
    test_message_2 = Message(
        id="test-uuid-2",
        timestamp=datetime.now(),
        collectionId="col2",
        collectionName="Collection 2",
        topic="LOG",
        message="Test log message 2"
    )

    # Configure the mock to return messages directly
    mock_asyncio_to_thread.side_effect = [test_message_1, test_message_2]

    response = client.get("/logs/stream")
    
    # Read events from the response
    received_events_raw_chunks = []
    async for chunk in response.aiter_bytes():
        received_events_raw_chunks.append(chunk.decode())
        if len(received_events_raw_chunks) == 1: # We expect one chunk containing both messages
            break

    # Manually parse the SSE events from the raw chunks
    parsed_events = []
    for raw_chunk in received_events_raw_chunks:
        # Split by the SSE delimiter and filter out empty strings
        events_in_chunk = [event for event in raw_chunk.split('\n\n') if event.strip()]
        parsed_events.extend(events_in_chunk)

    assert len(parsed_events) == 2
    assert parsed_events[0] == f"data: {test_message_1.model_dump_json()}" # No trailing \n\n
    assert parsed_events[1] == f"data: {test_message_2.model_dump_json()}" # No trailing \n\n

    mock_asyncio_to_thread.assert_called()

