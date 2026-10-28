import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from app.crud.crud_collection_content import get_collection_chunks, query_collection

@patch('chromadb.PersistentClient')
def test_get_collection_chunks_success(mock_persistent_client):
    """
    Test successful retrieval of paginated chunks from a collection.
    """
    # Arrange
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "ids": ["id1", "id2", "id3"],
        "documents": ["doc1", "doc2", "doc3"]
    }
    
    mock_client_instance = MagicMock()
    mock_client_instance.get_collection.return_value = mock_collection
    mock_persistent_client.return_value = mock_client_instance
    
    collection_id = "test_collection"
    page = 2
    page_size = 1
    
    # Act
    result = get_collection_chunks(collection_id, page, page_size)
    
    # Assert
    mock_persistent_client.assert_called_once_with(path="./chroma_data")
    mock_client_instance.get_collection.assert_called_once_with(name=collection_id)
    mock_collection.get.assert_called_once()
    
    assert result["total_chunks"] == 3
    assert result["page"] == page
    assert result["page_size"] == page_size
    assert result["chunks"][0]["id"] == "id2"
    assert result["chunks"][0]["document"] == "doc2"

@patch('chromadb.PersistentClient')
def test_get_collection_chunks_not_found(mock_persistent_client):
    """
    Test behavior when the collection is not found.
    """
    # Arrange
    mock_client_instance = MagicMock()
    mock_client_instance.get_collection.side_effect = ValueError("Collection not found")
    mock_persistent_client.return_value = mock_client_instance
    
    # Act & Assert
    with pytest.raises(ValueError, match="Collection 'test_collection' not found"):
        get_collection_chunks("test_collection", 1, 10)

@patch('app.crud.crud_collection_content.retrieve')
def test_query_collection_success(mock_retrieve):
    """
    Test successful querying of a collection.
    """
    # Arrange
    mock_retrieve.return_value = {"status": "success", "results": {"ids": [["chunk-1"]]}}
    collection_id = "test_collection"
    query_text = "test query"

    # Act
    result = query_collection(collection_id, query_text)

    # Assert
    mock_retrieve.assert_called_once_with(collection_id, query_text, n_results=10)
    assert result["status"] == "success"
    assert result["results"] == {"ids": [["chunk-1"]]}

@patch('app.crud.crud_collection_content.retrieve')
def test_query_collection_not_found(mock_retrieve):
    """
    Test query behavior when the collection is not found.
    """
    # Arrange
    mock_retrieve.side_effect = ValueError("Collection not found")

    # Act & Assert
    with pytest.raises(ValueError, match="Collection 'test_collection' not found"):
        query_collection("test_collection", "test query")
