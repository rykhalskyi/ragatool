import pytest
import asyncio
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch

from app.internal.tools import register_tools

@pytest.fixture
def mcp_manager():
    manager = MagicMock()
    manager.is_enabled.return_value = True
    return manager

@pytest.fixture
def captured_tools(mcp_manager):
    tools = {}
    
    class MockMcpServer:
        def tool(self, name=None):
            def decorator(func):
                tools[func.__name__] = func
                return func
            return decorator

    mock_server = MockMcpServer()
    register_tools(mock_server, mcp_manager)
    return tools

@pytest.mark.asyncio
class TestCallExtensionTool:

    @patch('app.internal.tools.ExtensionManager')
    async def test_call_extension_tool_success(self, MockExtensionManager, captured_tools):
        # Arrange
        call_extension_func = captured_tools['call_extension']
        mock_manager_instance = MockExtensionManager.return_value
        mock_manager_instance.send_command_and_wait_for_response = AsyncMock(return_value={"status": "success", "data": "result"})

        # Act
        result = await call_extension_func(id="ext_id", name="command_name", input={"key": "value"})

        # Assert
        assert result == {"status": "success", "data": "result"}
        mock_manager_instance.send_command_and_wait_for_response.assert_called_once_with(
            "ext_id", "command_name", {"key": "value"}, timeout=10
        )

    @patch('app.internal.tools.ExtensionManager')
    async def test_call_extension_connection_error(self, MockExtensionManager, captured_tools):
        # Arrange
        call_extension_func = captured_tools['call_extension']
        mock_manager_instance = MockExtensionManager.return_value
        mock_manager_instance.send_command_and_wait_for_response.side_effect = ConnectionError("Extension not found")
        
        # Act
        result = await call_extension_func(id="ext_id", name="command_name", input={"key": "value"})

        # Assert
        assert result == {"status": "error", "message": "Extension not found"}

    @patch('app.internal.tools.ExtensionManager')
    async def test_call_extension_timeout_error(self, MockExtensionManager, captured_tools):
        # Arrange
        call_extension_func = captured_tools['call_extension']
        mock_manager_instance = MockExtensionManager.return_value
        mock_manager_instance.send_command_and_wait_for_response.side_effect = asyncio.TimeoutError
        
        # Act
        result = await call_extension_func(id="ext_id", name="command_name", input={"key": "value"})

        # Assert
        assert result == {"status": "error", "message": "Command 'command_name' on extension 'ext_id' timed out after 10 seconds."}

    async def test_call_extension_missing_params(self, captured_tools):
        # Arrange
        call_extension_func = captured_tools['call_extension']
        
        # Act
        result_id = await call_extension_func(id=None, name="command_name", input={"key": "value"})
        result_name = await call_extension_func(id="ext_id", name=None, input={"key": "value"})
        result_input = await call_extension_func(id="ext_id", name="command_name", input=None)

        # Assert
        message = {"status": "error", "message": "Missing required parameters: id, name, or input."}
        assert result_id == message
        assert result_name == message
        assert result_input == message
        
    async def test_call_extension_mcp_disabled(self, captured_tools, mcp_manager):
        # Arrange
        mcp_manager.is_enabled.return_value = False
        # We need to re-register the tools to capture the correct state
        tools = {}
    
        class MockMcpServer:
            def tool(self, name=None):
                def decorator(func):
                    tools[func.__name__] = func
                    return func
                return decorator

        mock_server = MockMcpServer()
        register_tools(mock_server, mcp_manager)
        call_extension_func = tools['call_extension']

        # Act
        result = await call_extension_func(id="ext_id", name="command_name", input={"key": "value"})
        
        # Assert
        assert result == {"status": "error", "message": "MCP server is disabled."}

class TestAddFactTool:

    @patch('app.internal.tools.get_db_connection')
    @patch('app.internal.tools.get_collection_by_name')
    @patch('app.internal.tools.create_collection')
    @patch('app.internal.tools.chromadb.PersistentClient')
    @patch('app.internal.tools.get_embedder')
    def test_add_fact_success(self, mock_get_embedder, mock_chroma_client, mock_create_collection, mock_get_collection_by_name, mock_get_db, captured_tools):
        # Arrange
        add_fact_func = captured_tools['add_fact']
        mock_get_collection_by_name.return_value = None # Simulate collection missing
        
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        mock_collection = MagicMock()
        mock_chroma_client.return_value.get_collection.return_value = mock_collection
        
        mock_embedder = MagicMock()
        mock_get_embedder.return_value = mock_embedder
        mock_embedder.embed.return_value = iter([np.array([0.1, 0.2, 0.3])])

        # Act
        result = add_fact_func(fact="User likes pizza", summary="User's food preference")

        # Assert
        assert result["status"] == "success"
        mock_create_collection.assert_called_once()
        mock_collection.add.assert_called_once()
        args, kwargs = mock_collection.add.call_args
        assert kwargs['documents'] == ["User likes pizza"]
        assert kwargs['metadatas'][0]['summary'] == "User's food preference"
        assert 'embeddings' in kwargs

    def test_add_fact_mcp_disabled(self, captured_tools, mcp_manager):
        # Arrange
        mcp_manager.is_enabled.return_value = False
        tools = {}
        class MockMcpServer:
            def tool(self, name=None):
                def decorator(func):
                    tools[func.__name__] = func
                    return func
                return decorator
        register_tools(MockMcpServer(), mcp_manager)
        add_fact_func = tools['add_fact']

        # Act
        result = add_fact_func(fact="User likes pizza", summary="User's food preference")
        
        # Assert
        assert result == {"status": "error", "message": "MCP server is disabled."}

class TestGetSummaryTool:

    @patch('app.internal.tools.get_db_connection')
    @patch('app.internal.tools.get_summary_by_type')
    def test_get_summaries_returns_all_summaries(self, mock_get_summary_by_type, mock_get_db, captured_tools):
        # Arrange
        get_summaries_func = captured_tools['get_summaries']
        
        from app.schemas.summary import Summary, SummaryType
        
        mock_summaries = [
            Summary(id="1", collection_id="test_col", type=SummaryType.TOC, summary="TOC 1"),
            Summary(id="2", collection_id="test_col", type=SummaryType.TOC, summary="TOC 2"),
        ]
        mock_get_summary_by_type.return_value = mock_summaries
        
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Act
        result = get_summaries_func(collection_name="test_col", summary_type=2)  # 2 = SummaryType.TOC
        
        # Assert
        assert result["status"] == "success"
        assert "summaries" in result
        assert len(result["summaries"]) == 2
        assert result["summaries"][0]["summary"] == "TOC 1"
        assert result["summaries"][1]["summary"] == "TOC 2"
        mock_get_summary_by_type.assert_called_once()

    @patch('app.internal.tools.get_db_connection')
    @patch('app.internal.tools.get_summary_by_type')
    def test_get_summaries_empty_list(self, mock_get_summary_by_type, mock_get_db, captured_tools):
        # Arrange
        get_summaries_func = captured_tools['get_summaries']
        
        mock_get_summary_by_type.return_value = []
        
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Act
        result = get_summaries_func(collection_name="test_col", summary_type=2)
        
        # Assert
        assert result["status"] == "error"
        assert "No summaries found" in result["message"]

    def test_get_summaries_invalid_type(self, captured_tools):
        # Arrange
        get_summaries_func = captured_tools['get_summaries']
        
        # Act
        result = get_summaries_func(collection_name="test_col", summary_type=99)
        
        # Assert
        assert result["status"] == "error"
        assert "Invalid summary type" in result["message"]

    def test_get_summaries_mcp_disabled(self, mcp_manager):
        # Arrange
        mcp_manager.is_enabled.return_value = False
        tools = {}
        class MockMcpServer:
            def tool(self, name=None):
                def decorator(func):
                    tools[func.__name__] = func
                    return func
                return decorator
        register_tools(MockMcpServer(), mcp_manager)
        get_summaries_func = tools['get_summaries']

        # Act
        result = get_summaries_func(collection_name="test_col", summary_type=2)
        
        # Assert
        assert result == {"status": "error", "message": "MCP server is disabled."}

class TestWikiTools:

    @patch('app.internal.tools.get_db_connection')
    @patch('app.internal.tools.create_summary')
    def test_add_wiki_page_success(self, mock_create_summary, mock_get_db, captured_tools):
        # Arrange
        add_wiki_func = captured_tools['add_wiki_page']
        
        from app.schemas.summary import Summary, SummaryType
        mock_summary = Summary(id="wiki_123", collection_id="test_col", type=SummaryType.WIKI, summary="content", metadata="{}")
        mock_create_summary.return_value = mock_summary
        
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Act
        result = add_wiki_func(collection_id="Test Col", page_title="My Title", type="Character", tags=["tag1"], text="Wiki content")
        
        # Assert
        assert result["status"] == "success"
        assert result["page_id"] == "wiki_123"
        mock_create_summary.assert_called_once()
        args, _ = mock_create_summary.call_args
        passed_summary = args[1]
        assert passed_summary.collection_id == "test_col"
        assert passed_summary.type == SummaryType.WIKI
        assert passed_summary.summary == "Wiki content"
        import json
        meta = json.loads(passed_summary.metadata)
        assert meta["title"] == "My Title"
        assert meta["type"] == "Character"
        assert meta["tags"] == ["tag1"]

    @patch('app.internal.tools.get_db_connection')
    @patch('app.internal.tools.get_summary_by_id')
    @patch('app.internal.tools.edit_summary')
    def test_edit_wiki_page_success(self, mock_edit_summary, mock_get_summary_by_id, mock_get_db, captured_tools):
        # Arrange
        edit_wiki_func = captured_tools['edit_wiki_page']
        
        from app.schemas.summary import Summary, SummaryType
        mock_existing = Summary(id="wiki_123", collection_id="test_col", type=SummaryType.WIKI, summary="old", metadata="{}")
        mock_get_summary_by_id.return_value = mock_existing
        
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Act
        result = edit_wiki_func(page_id="wiki_123", page_title="New Title", type="Location", tags=["tag2"], text="New content")
        
        # Assert
        assert result["status"] == "success"
        mock_edit_summary.assert_called_once()
        args, _ = mock_edit_summary.call_args
        passed_summary = args[2]
        assert passed_summary.id == "wiki_123"
        assert passed_summary.summary == "New content"
        import json
        meta = json.loads(passed_summary.metadata)
        assert meta["title"] == "New Title"

    @patch('app.internal.tools.get_db_connection')
    @patch('app.internal.tools.get_summary_by_id')
    def test_get_wiki_page_success(self, mock_get_summary_by_id, mock_get_db, captured_tools):
        # Arrange
        get_wiki_func = captured_tools['get_wiki_page']
        
        from app.schemas.summary import Summary, SummaryType
        import json
        metadata = json.dumps({"title": "Test Wiki", "type": "Plot", "tags": ["important"]})
        mock_summary = Summary(id="wiki_123", collection_id="test_col", type=SummaryType.WIKI, summary="Wiki text", metadata=metadata)
        mock_get_summary_by_id.return_value = mock_summary
        
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Act
        result = get_wiki_func(page_id="wiki_123")
        
        # Assert
        assert result["status"] == "success"
        assert result["result"]["title"] == "Test Wiki"
        assert result["result"]["text"] == "Wiki text"
        assert result["result"]["tags"] == ["important"]

    @patch('app.internal.tools.get_db_connection')
    @patch('app.internal.tools.get_summary_by_id')
    def test_get_wiki_page_not_found(self, mock_get_summary_by_id, mock_get_db, captured_tools):
        # Arrange
        get_wiki_func = captured_tools['get_wiki_page']
        mock_get_summary_by_id.return_value = None
        
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Act
        result = get_wiki_func(page_id="nonexistent")
        
        # Assert
        assert result["status"] == "error"
        assert "not found" in result["message"]
