import json

import pytest

from app.internal.agent import tool_bridge


@pytest.mark.asyncio
async def test_tool_list_excludes_health_check_and_has_schemas():
    tools = await tool_bridge.list_openai_tools()
    names = {tool["function"]["name"] for tool in tools}

    assert "query_collection" in names
    assert "get_chunks_by_id" in names
    assert "health_check" not in names

    query = next(
        tool for tool in tools if tool["function"]["name"] == "query_collection"
    )
    assert query["type"] == "function"
    assert query["function"]["parameters"]["type"] == "object"


@pytest.mark.asyncio
async def test_tool_list_is_read_only():
    tools = await tool_bridge.list_openai_tools()
    names = {tool["function"]["name"] for tool in tools}

    assert names == tool_bridge.READ_ONLY_TOOLS
    assert "delete_summary" not in names
    assert "edit_wiki_page" not in names
    assert "add_to_collection" not in names
    assert "call_extension" not in names


@pytest.mark.asyncio
async def test_execute_tool_rejects_mutating_tools():
    for name in ("delete_summary", "edit_wiki_page", "add_fact", "call_extension"):
        result = await tool_bridge.execute_tool(name, {})

        assert result["ok"] is False
        payload = json.loads(result["content"])
        assert payload["status"] == "error"
        assert name in payload["message"]


@pytest.mark.asyncio
async def test_execute_unknown_tool_returns_structured_error():
    result = await tool_bridge.execute_tool("does_not_exist", {})

    assert result["ok"] is False
    payload = json.loads(result["content"])
    assert payload["status"] == "error"
    assert "does_not_exist" in payload["message"]


@pytest.mark.asyncio
async def test_tool_bridge_runs_with_mcp_disabled(tmp_path, monkeypatch):
    import app.database as database
    from app.internal.mcp_manager import mcp_manager

    monkeypatch.setattr(database, "DATABASE_URL", str(tmp_path / "agent.db"))
    database.create_tables()
    monkeypatch.setattr(mcp_manager, "_is_enabled", False)

    result = await tool_bridge.execute_tool("collection_list", {})

    assert result["ok"] is True
    assert json.loads(result["content"]) == []


def test_preview_collapses_and_truncates():
    short = tool_bridge.preview("line one\nline two")
    assert short == "line one line two"

    long = tool_bridge.preview("x" * (tool_bridge.MAX_TOOL_PREVIEW_CHARS + 50))
    assert long.endswith("...")
    assert len(long) <= tool_bridge.MAX_TOOL_PREVIEW_CHARS + 3
