import sys
import os
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.version import APP_NAME, APP_VERSION

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": APP_NAME, "version": APP_VERSION}


def test_read_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"name": APP_NAME, "version": APP_VERSION}
