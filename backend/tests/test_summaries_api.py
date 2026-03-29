import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app as fastapi_app
from app.dependencies import get_db
import app.database
import chromadb
import tempfile
from app.schemas.summary import SummaryType

@pytest.fixture(scope="function")
def client():
    with patch('app.database.DATABASE_URL', ":memory:"):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('chromadb.PersistentClient') as mock_persistent_client:
                mock_persistent_client.return_value = chromadb.PersistentClient(path=tmpdir)
                connection = app.database.get_db_connection()
                app.database.create_tables(connection)

                def override_get_db():
                    try:
                        yield connection
                    finally:
                        pass

                fastapi_app.dependency_overrides[get_db] = override_get_db
                yield TestClient(fastapi_app)
                fastapi_app.dependency_overrides.clear()
                connection.close()

def teardown_module(module):
    pass

def test_create_summary(client):
    response = client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.BOOK.value,
        "summary": "This is a book summary",
        "metadata": "some metadata"
    })
    assert response.status_code == 200
    summary_id = response.json()
    assert isinstance(summary_id, str)

def test_get_summaries_by_collection(client):
    # Create two summaries for the same collection
    client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.BOOK.value,
        "summary": "Book summary",
        "metadata": None
    })
    client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.CHAPTER.value,
        "summary": "Chapter summary",
        "metadata": None
    })
    # Create one for different collection
    client.post("/summaries/", json={
        "collection_id": "other_col",
        "type": SummaryType.BOOK.value,
        "summary": "Other book summary",
        "metadata": None
    })

    response = client.get("/summaries/collection/test_col")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    summaries = [s["summary"] for s in data]
    assert "Book summary" in summaries
    assert "Chapter summary" in summaries

def test_get_summaries_by_type(client):
    client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.BOOK.value,
        "summary": "Book summary",
        "metadata": None
    })
    client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.CHAPTER.value,
        "summary": "Chapter summary",
        "metadata": None
    })

    response = client.get(f"/summaries/collection/test_col/type/{SummaryType.BOOK.value}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["summary"] == "Book summary"
    assert data[0]["type"] == SummaryType.BOOK.value

def test_update_summary(client):
    # Create a summary first
    resp = client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.BOOK.value,
        "summary": "Old summary",
        "metadata": "old meta"
    })
    summary_id = resp.json()

    # Update it
    update_resp = client.put(f"/summaries/{summary_id}", json={
        "type": SummaryType.CHAPTER.value,
        "summary": "New summary",
        "metadata": "new meta"
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "success"

    # Verify update
    get_resp = client.get("/summaries/collection/test_col")
    data = get_resp.json()
    assert data[0]["summary"] == "New summary"
    assert data[0]["type"] == SummaryType.CHAPTER.value
    assert data[0]["metadata"] == "new meta"

def test_delete_summary(client):
    # Create a summary
    resp = client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.BOOK.value,
        "summary": "To be deleted",
        "metadata": None
    })
    summary_id = resp.json()

    # Delete it
    delete_resp = client.delete(f"/summaries/{summary_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "success"

    # Verify deletion
    get_resp = client.get("/summaries/collection/test_col")
    assert len(get_resp.json()) == 0
