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

def test_graph_manager_get_credentials_defaults():
    # Ensure environment variables are not set during this test
    with patch.dict(os.environ, {}, clear=True):
        gm = GraphManager()
        uri, user, password = gm._get_credentials()
        
        assert uri == "bolt://localhost:7687"
        assert user == "neo4j"
        assert password == None
