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

def test_create_summary(client):
    response = client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.BOOK.value,
        "summary": "This is a book summary",
        "metadata": "some metadata"
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["collection_id"] == "test_col"
    assert data["summary"] == "This is a book summary"

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

    response = client.get("/summaries/collection/test_col")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_get_summaries_by_type(client):
    client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.BOOK.value,
        "summary": "Book summary",
        "metadata": None
    })
    
    response = client.get(f"/summaries/collection/test_col/type/{SummaryType.BOOK.value}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["summary"] == "Book summary"

def test_update_summary(client):
    # Create a summary first
    resp = client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.BOOK.value,
        "summary": "Old summary",
        "metadata": "old meta"
    })
    summary_id = resp.json()["id"]

    # Update it
    update_resp = client.put(f"/summaries/{summary_id}", json={
        "type": SummaryType.CHAPTER.value,
        "summary": "New summary",
        "metadata": "new meta"
    })
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["summary"] == "New summary"

def test_update_summary_not_found(client):
    update_resp = client.put("/summaries/non_existent_id", json={
        "type": SummaryType.CHAPTER.value,
        "summary": "New summary",
        "metadata": "new meta"
    })
    assert update_resp.status_code == 404

def test_delete_summary(client):
    # Create a summary
    resp = client.post("/summaries/", json={
        "collection_id": "test_col",
        "type": SummaryType.BOOK.value,
        "summary": "To be deleted",
        "metadata": None
    })
    summary_id = resp.json()["id"]

    # Delete it
    delete_resp = client.delete(f"/summaries/{summary_id}")
    assert delete_resp.status_code == 200

    # Verify deletion
    get_resp = client.get("/summaries/collection/test_col")
    assert len(get_resp.json()) == 0

def test_delete_summary_not_found(client):
    delete_resp = client.delete("/summaries/non_existent_id")
    assert delete_resp.status_code == 404
