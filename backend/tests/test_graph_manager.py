import pytest
import os
from unittest.mock import MagicMock, patch
from app.internal.graph_manager import GraphManager

def test_graph_manager_init():
    gm = GraphManager()
    assert gm._driver is None

@patch.dict(os.environ, {
    "RAG_NEO4J_URI": "bolt://test-uri:7687",
    "RAG_NEO4J_USER": "test-user",
    "RAG_NEO4J_PASSWORD": "test-password"
})
def test_graph_manager_get_credentials_env():
    gm = GraphManager()
    uri, user, password = gm._get_credentials()
    
    assert uri == "bolt://test-uri:7687"
    assert user == "test-user"
    assert password == "test-password"

def test_graph_manager_singleton():
    gm1 = GraphManager()
    gm2 = GraphManager()
    assert gm1 is gm2

def test_graph_manager_get_credentials_defaults():
    # Ensure environment variables are not set during this test
    with patch.dict(os.environ, {}, clear=True):
        gm = GraphManager()
        uri, user, password = gm._get_credentials()
        
        assert uri == "bolt://localhost:7687"
        assert user == "neo4j"
        assert password == None

def test_validate_label():
    gm = GraphManager()
    gm._validate_label("PERSON") # Should not raise
    with pytest.raises(ValueError):
        gm._validate_label("INVALID_LABEL")

def test_validate_relation():
    gm = GraphManager()
    gm._validate_relation("MENTIONS") # Should not raise
    with pytest.raises(ValueError):
        gm._validate_relation("INVALID_RELATION")

@patch("app.internal.graph_manager.GraphDatabase")
def test_create_node_mocked(mock_db):
    gm = GraphManager()
    mock_driver = MagicMock()
    gm._driver = mock_driver
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    gm.create_node("PERSON", {"id": "dracula", "name": "Dracula"})
    
    mock_session.run.assert_called_once()
    query = mock_session.run.call_args[0][0]
    props = mock_session.run.call_args[1]["props"]
    
    assert "MERGE (n:PERSON {id: $props.id})" in query
    assert props["id"] == "dracula"

@patch("app.internal.graph_manager.GraphDatabase")
def test_create_edge_mocked(mock_db):
    gm = GraphManager()
    mock_driver = MagicMock()
    gm._driver = mock_driver
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    gm.create_edge("chunk1", "dracula", "MENTIONS", src_label="CHUNK", dst_label="PERSON")
    
    mock_session.run.assert_called_once()
    query = mock_session.run.call_args[0][0]
    kwargs = mock_session.run.call_args[1]
    
    assert "MATCH (a:CHUNK {id: $src_id}), (b:PERSON {id: $dst_id})" in query
    assert "MERGE (a)-[r:MENTIONS]->(b)" in query
    assert kwargs["src_id"] == "chunk1"
    assert kwargs["dst_id"] == "dracula"

@patch("app.internal.graph_manager.GraphDatabase")
def test_delete_collection_mocked(mock_db):
    gm = GraphManager()
    mock_driver = MagicMock()
    gm._driver = mock_driver
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    collection_id = "test_col"
    gm.delete_collection(collection_id)
    
    mock_session.run.assert_called_once()
    query = mock_session.run.call_args[0][0]
    kwargs = mock_session.run.call_args[1]
    
    assert "MATCH (c:COLLECTION {id: $collection_id})" in query
    assert "OPTIONAL MATCH (c)-[:CONTAINS]->(n)" in query
    assert "DETACH DELETE c, n" in query
    assert kwargs["collection_id"] == collection_id

@patch("app.internal.graph_manager.GraphDatabase")
def test_add_chapter_mocked(mock_db):
    gm = GraphManager()
    mock_driver = MagicMock()
    gm._driver = mock_driver
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    gm.add_chapter("Chapter 1", "col1", "Summary text", 1)
    
    # add_chapter calls create_node and create_edge
    assert mock_session.run.call_count == 2
    
    # First call should be create_node for CHAPTER
    args0 = mock_session.run.call_args_list[0]
    query0 = args0[0][0]
    props0 = args0[1]["props"]
    assert "MERGE (n:CHAPTER {id: $props.id})" in query0
    assert props0["id"] == "Chapter 1_1"
    assert props0["name"] == "Chapter 1"
    assert props0["summary"] == "Summary text"
    
    # Second call should be create_edge for CONTAINS
    args1 = mock_session.run.call_args_list[1]
    query1 = args1[0][0]
    kwargs1 = args1[1]
    assert "MATCH (a:COLLECTION {id: $src_id}), (b:CHAPTER {id: $dst_id})" in query1
    assert "MERGE (a)-[r:CONTAINS]->(b)" in query1
    assert kwargs1["src_id"] == "col1"
    assert kwargs1["dst_id"] == "Chapter 1_1"
