import json
import threading
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from app.internal.tools import register_tools

MAX_TOOL_RESULT_CHARS = 24_000
MAX_TOOL_PREVIEW_CHARS = 600

# The built-in agent only gets read-only tools. Mutating tools and
# `call_extension` are intentionally excluded so that untrusted document text
# cannot trick the model into deleting data or invoking extensions.
READ_ONLY_TOOLS = {
    "collection_list",
    "extension_list",
    "get_chunks_by_id",
    "get_single_summary",
    "get_summaries",
    "get_table_of_contents",
    "get_wiki_index",
    "get_wiki_page",
    "query_collection",
}


class _AlwaysEnabledManager:
    """Adapter that keeps the read-only agent toolset independent of MCP ON."""

    server_name = "Rag-a-Tool-Agent"

    def is_enabled(self) -> bool:
        return True


_server: FastMCP | None = None
_server_lock = threading.Lock()


def get_server() -> FastMCP:
    global _server
    if _server is None:
        with _server_lock:
            if _server is None:
                server = FastMCP("Rag-a-Tool-Agent")
                register_tools(server, _AlwaysEnabledManager())
                _server = server
    return _server


def _truncate(text: str, limit: int = MAX_TOOL_RESULT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[tool result truncated]"


def _dump(value: Any) -> str:
    if isinstance(value, str):
        return _truncate(value)
    try:
        return _truncate(json.dumps(value, ensure_ascii=False, default=str))
    except (TypeError, ValueError):
        return _truncate(str(value))


def _result_text(result: Any) -> str:
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        if isinstance(structured, dict) and set(structured) == {"result"}:
            return _dump(structured["result"])
        return _dump(structured)

    content = getattr(result, "content", None) or []
    texts = [
        item.text
        for item in content
        if isinstance(getattr(item, "text", None), str)
    ]
    if texts:
        return _truncate("\n".join(texts))
    return _dump(content)


def preview(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= MAX_TOOL_PREVIEW_CHARS:
        return collapsed
    return collapsed[:MAX_TOOL_PREVIEW_CHARS] + "..."


async def list_openai_tools() -> list[dict[str, Any]]:
    """Return the private toolset as OpenAI-compatible function definitions."""
    tools = await get_server().list_tools()
    definitions: list[dict[str, Any]] = []
    for tool in tools:
        if tool.name not in READ_ONLY_TOOLS:
            continue
        parameters = getattr(tool, "parameters", None) or {
            "type": "object",
            "properties": {},
        }
        definitions.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": parameters,
                },
            }
        )
    return definitions


async def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute one tool in-process and return a model-safe result envelope."""
    if name not in READ_ONLY_TOOLS:
        return {
            "ok": False,
            "content": json.dumps(
                {"status": "error", "message": f"Tool '{name}' is not available."}
            ),
            "error": "unsupported tool",
        }

    try:
        result = await get_server().call_tool(name, arguments or {})
    except ToolError as exc:
        message = str(exc)
        return {
            "ok": False,
            "content": json.dumps({"status": "error", "message": message}),
            "error": message,
        }
    except Exception:  # noqa: BLE001 - tool failures must not abort chat
        message = f"Tool '{name}' failed."
        return {
            "ok": False,
            "content": json.dumps({"status": "error", "message": message}),
            "error": message,
        }

    content = _result_text(result)
    return {"ok": True, "content": content, "error": None}
