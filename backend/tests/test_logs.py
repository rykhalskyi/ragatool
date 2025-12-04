import sys
import os
from fastapi.testclient import TestClient
import pytest
import sqlite3
from unittest.mock import patch
from app.database import get_db_connection, create_tables
from app.crud.crud_log import create_log
from app.dependencies import get_db # Import the actual dependency to override

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

client = TestClient(app)

@pytest.fixture(scope="function")
def get_test_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    create_tables(conn)  # Assuming create_tables can take a connection object
    
    # Create some test data
    for i in range(15):
        create_log(conn, f"coll_id_{i}", "test", f"test message {i}")
    
    yield conn
    conn.close()

@pytest.fixture(scope="function", autouse=True)
def override_dependency(get_test_db):
    app.dependency_overrides[get_db] = lambda: get_test_db
    yield
    app.dependency_overrides.clear()

def test_read_logs_default():
    response = client.get("/logs/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 10

def test_read_logs_with_n_parameter():
    response = client.get("/logs/?n=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5

def test_read_logs_with_large_n():
    response = client.get("/logs/?n=20")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # We only created 15 log entries
    assert len(data) == 15
