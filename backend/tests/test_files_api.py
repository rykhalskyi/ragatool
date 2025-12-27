import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app  # Assuming your FastAPI app is named 'app' in 'main.py'
from app.internal.temp_file_helper import TempFileHelper

client = TestClient(app)

@pytest.fixture
def mock_temp_file_helper():
    with patch('app.routers.files.TempFileHelper') as mock_helper:
        yield mock_helper

def test_get_chunk_preview_success(mock_temp_file_helper):
    """
    Test successful chunk preview generation.
    """
    # Arrange
    test_content = "This is a test content that will be split into chunks." * 5
    mock_temp_file_helper.get_temp_file_content.return_value = test_content
    
    request_payload = {
        "file_id": "existing_file.txt",
        "skip_number": 0,
        "take_number": 2,
        "chunk_size": 50,
        "chunk_overlap": 5,
        "no_chunks": False
    }

    # Act
    response = client.post("/files/content", json=request_payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "chunks" in data
    assert "more_chunks" in data
    assert len(data["chunks"]) == 2
    assert data["chunks"][0] == "This is a test content that will be split into chu"
    assert data["more_chunks"] is True
    mock_temp_file_helper.get_temp_file_content.assert_called_once_with("existing_file.txt")

def test_get_chunk_preview_file_not_found(mock_temp_file_helper):
    """
    Test the case where the temporary file is not found (404).
    """
    # Arrange
    mock_temp_file_helper.get_temp_file_content.side_effect = FileNotFoundError
    
    request_payload = {
        "file_id": "non_existent_file.txt",
        "skip_number": 0,
        "take_number": 2,
        "chunk_size": 50,
        "chunk_overlap": 5,
        "no_chunks": False
    }

    # Act
    response = client.post("/files/content", json=request_payload)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Temporary file not found."}

def test_get_chunk_preview_invalid_params(mock_temp_file_helper):
    """
    Test the case with invalid request parameters (422).
    """
    # Arrange
    mock_temp_file_helper.get_temp_file_content.return_value = "some content"
    request_payload = {
        "file_id": "any_file.txt",
        "skip_number": 0,
        "take_number": 2,
        "chunk_size": -100,  # Invalid chunk size
        "chunk_overlap": 5,
        "no_chunks": False
    }

    # Act
    response = client.post("/files/content", json=request_payload)

    # Assert
    assert response.status_code == 422  # Unprocessable Entity

def test_get_chunk_preview_no_chunks_mode(mock_temp_file_helper):
    """
    Test the 'no_chunks' mode where the entire content is returned as a single chunk.
    """
    # Arrange
    test_content = "This is the full content."
    mock_temp_file_helper.get_temp_file_content.return_value = test_content

    request_payload = {
        "file_id": "some_file.txt",
        "skip_number": 0,
        "take_number": 1,
        "chunk_size": 100,
        "chunk_overlap": 10,
        "no_chunks": True
    }

    # Act
    response = client.post("/files/content", json=request_payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["chunks"]) == 1
    assert data["chunks"][0] == test_content
    assert data["more_chunks"] is False
