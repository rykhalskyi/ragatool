import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app as fastapi_app
from app.dependencies import get_db
import app.database
import chromadb
import tempfile
import uuid

# Mock MCPManager globally
mock_mcp_manager = MagicMock()
mcp_manager_patch = patch('app.routers.collections.mcp_manager', mock_mcp_manager)
mcp_manager_patch.start()

# Patch the DATABASE_URL to use an in-memory database for all tests
database_url_patch = patch('app.database.DATABASE_URL', ":memory:")
database_url_patch.start()

@pytest.fixture(scope="function")
def client():
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
            mock_mcp_manager.reset_mock()

def teardown_module(module):
    mcp_manager_patch.stop()
    database_url_patch.stop()

def test_create_collection_success(client):
    response = client.post("/collections/", json={
        "name": "My New Collection", "description": "A test collection", "enabled": True, "model": "test_model", "settings": "{}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My New Collection"
    assert "id" in data

def test_create_duplicate_collection_fails(client):
    client.post("/collections/", json={"name": "Unique Name"})
    response = client.post("/collections/", json={"name": "Unique Name"})
    assert response.status_code == 409

def test_delete_collection(client):
    create_response = client.post("/collections/", json={"name": "To Be Deleted"})
    collection_id = create_response.json()["id"]
    delete_response = client.delete(f"/collections/{collection_id}")
    assert delete_response.status_code == 200
    get_response = client.get(f"/collections/{collection_id}")
    assert get_response.status_code == 404

def test_read_collection_details(client):
    create_response = client.post("/collections/", json={"name": "Details Test"})
    collection_id = create_response.json()["id"]
    with patch('chromadb.PersistentClient') as mock_persistent_client:
        mock_collection = mock_persistent_client.return_value.get_collection.return_value
        mock_collection.count.return_value = 42
        mock_collection.metadata = {"source": "api_test"}
        response = client.get(f"/collections/{collection_id}/details")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Details Test"
        assert data["count"] == 42
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"/collections/{non_existent_id}/details")
    assert response.status_code == 404

@patch('app.routers.collections.get_collection_chunks')
def test_read_collection_content_success(mock_get_chunks, client):
    create_response = client.post("/collections/", json={"name": "Content Test"})
    assert create_response.status_code == 200
    collection_id = create_response.json()["id"]

    mock_get_chunks.return_value = {
        "chunks": [{"id": "1", "document": "doc1"}],
        "total_chunks": 1,
        "page": 1,
        "page_size": 10
    }
    
    response = client.post(f"/collections/{collection_id}/content", json={"page": 1, "page_size": 10})
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_chunks"] == 1
    mock_get_chunks.assert_called_once_with(collection_id, 1, 10)

def test_read_collection_content_not_found(client):
    import uuid
    non_existent_id = str(uuid.uuid4())
    response = client.post(f"/collections/{non_existent_id}/content", json={"page": 1, "page_size": 10})
    assert response.status_code == 404

@patch('app.routers.collections.query_collection')
def test_query_collection_success(mock_query_collection, client):
    create_response = client.post("/collections/", json={"name": "Query Test"})
    assert create_response.status_code == 200
    collection_id = create_response.json()["id"]
    
    mock_query_collection.return_value = {"status": "success", "results": "mocked_results"}
    
    response = client.get(f"/collections/{collection_id}/query?query_text=hello")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    mock_query_collection.assert_called_once_with(collection_id, "hello")

def test_query_collection_not_found(client):
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"/collections/{non_existent_id}/query?query_text=hello")
    assert response.status_code == 404

