import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app as fastapi_app # Import the FastAPI app instance
from app.dependencies import get_db
import app.database # Import the database module
import chromadb # Import chromadb
import tempfile # Import tempfile
import shutil # Import shutil


# Mock MCPManager globally
mock_mcp_manager = MagicMock()
mcp_manager_patch = patch('app.routers.collections.mcp_manager', mock_mcp_manager)
mcp_manager_patch.start() # Start the patch once for the module

# Patch the DATABASE_URL to use an in-memory database for all tests
database_url_patch = patch('app.database.DATABASE_URL', ":memory:")
database_url_patch.start()

@pytest.fixture(scope="function")
def client():
    # Create a temporary directory for ChromaDB
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch chromadb.PersistentClient to use the temporary directory
        with patch('chromadb.PersistentClient') as mock_persistent_client:
            mock_persistent_client.return_value = chromadb.PersistentClient(path=tmpdir)

            # Use a fresh in-memory database for each test function
            connection = app.database.get_db_connection()
            app.database.create_tables(connection) # Use the patched DATABASE_URL

            def override_get_db():
                try:
                    yield connection
                finally:
                    # Removed connection.close() here; in-memory db is ephemeral per fixture call
                    pass


            fastapi_app.dependency_overrides[get_db] = override_get_db
            yield TestClient(fastapi_app)
            fastapi_app.dependency_overrides.clear()
            mock_mcp_manager.reset_mock() # Reset mock calls between tests

# Stop the patches after all tests in the module are done
def teardown_module(module):
    mcp_manager_patch.stop()
    database_url_patch.stop()

def test_create_collection_success(client):
    response = client.post("/collections/", json={
        "name": "My New Collection",
        "description": "A test collection",
        "enabled": True,
        "model": "test_model",
        "settings": "{}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My New Collection" # Expect original name
    assert "id" in data

def test_create_duplicate_collection_fails(client):
    # First, create a collection
    client.post("/collections/", json={
        "name": "Unique Name",
        "description": "A test collection",
        "enabled": True,
        "model": "test_model",
        "settings": "{}"
    })

    # Then, attempt to create another with the same name
    response = client.post("/collections/", json={
        "name": "Unique Name",
        "description": "Another collection",
        "enabled": False,
        "model": "another_model",
        "settings": "{}"
    })
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

def test_create_duplicate_collection_case_insensitive_fails(client):
    # Create a collection with a specific casing
    client.post("/collections/", json={
        "name": "Case Test",
        "description": "A test collection",
        "enabled": True,
        "model": "test_model",
        "settings": "{}"
    })

    # Attempt to create with different casing
    response = client.post("/collections/", json={
        "name": "case test",
        "description": "Another collection",
        "enabled": False,
        "model": "another_model",
        "settings": "{}"
    })
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

def test_delete_collection(client):
    # Create a collection to delete
    create_response = client.post("/collections/", json={
        "name": "To Be Deleted",
        "description": "This will be removed",
        "enabled": True,
        "model": "delete_model",
        "settings": "{}"
    })
    collection_id = create_response.json()["id"]

    # Reset the mock before the delete call to check it was called
    mock_mcp_manager.delete_collection.reset_mock()

    # Delete the collection
    delete_response = client.delete(f"/collections/{collection_id}")
    assert delete_response.status_code == 200

    # Verify the collection is gone
    get_response = client.get(f"/collections/{collection_id}")
    assert get_response.status_code == 404

