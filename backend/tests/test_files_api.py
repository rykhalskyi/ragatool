import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.schemas.file import File

client = TestClient(app)

@pytest.fixture
def mock_get_file():
    with patch('app.routers.files.get_file') as mock_get:
        yield mock_get

@pytest.fixture
def mock_temp_file_helper():
    with patch('app.routers.files.TempFileHelper') as mock_helper:
        yield mock_helper

def test_get_chunk_preview_success(mock_get_file, mock_temp_file_helper):
    """
    Test successful chunk preview generation.
    """
    # Arrange
    test_content = "This is a test content that will be split into chunks." * 5
    mock_temp_file_helper.get_temp_file_content.return_value = test_content
    
    mock_file = File(id="existing_file.txt", path="/path/to/existing_file.txt", collection_id="123", timestamp="2023-01-01T12:00:00", source="existing_file.txt")
    mock_get_file.return_value = mock_file
    
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
    mock_temp_file_helper.get_temp_file_content.assert_called_once_with(mock_file.path)

def test_get_chunk_preview_file_not_found_in_db(mock_get_file):
    """
    Test the case where the file is not found in the database.
    """
    # Arrange
    mock_get_file.return_value = None
    
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
    assert response.status_code == 500 # Because it will raise an AttributeError

def test_get_chunk_preview_file_not_found_on_disk(mock_get_file, mock_temp_file_helper):
    """
    Test the case where the file is not found on disk (404).
    """
    # Arrange
    mock_file = File(id="existing_file.txt", path="/path/to/existing_file.txt", collection_id="123", timestamp="2023-01-01T12:00:00", source="existing_file.txt")
    mock_get_file.return_value = mock_file
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

def test_get_chunk_preview_invalid_params(mock_get_file, mock_temp_file_helper):
    """
    Test the case with invalid request parameters (422).
    """
    # Arrange
    mock_file = File(id="any_file.txt", path="/path/to/any_file.txt", collection_id="123", timestamp="2023-01-01T12:00:00", source="any_file.txt")
    mock_get_file.return_value = mock_file
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

def test_get_chunk_preview_no_chunks_mode(mock_get_file, mock_temp_file_helper):
    """
    Test the 'no_chunks' mode where the entire content is returned as a single chunk.
    """
    # Arrange
    test_content = "This is the full content."
    mock_temp_file_helper.get_temp_file_content.return_value = test_content
    mock_file = File(id="some_file.txt", path="/path/to/some_file.txt", collection_id="123", timestamp="2023-01-01T12:00:00", source="some_file.txt")
    mock_get_file.return_value = mock_file

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