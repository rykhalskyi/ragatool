import sys
import os
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

client = TestClient(app)

def test_read_items():
    response = client.get("/items/")
    assert response.status_code == 200
    collections = response.json()
    assert isinstance(collections, list)
    # Assert that each collection has the expected keys
    for collection in collections:
        assert "name" in collection
        assert "description" in collection
        assert "properties" in collection
