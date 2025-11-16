from fastmcp import FastMCP
import threading
import time
from app.database import get_db_connection
from app.crud.crud_collection import get_enabled_collections_for_mcp

class MCPManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._mcp_server: FastMCP | None = None
        self._is_enabled: bool = False
        self._server_thread: threading.Thread | None = None
        self.server_name = "Ragatouille"

    def _run_server(self):
        if self._mcp_server:
            # FastMCP.run() is a blocking call, so it needs to be in a separate thread
            self._mcp_server.run(transport="sse", host="127.0.0.1", port=8001, path="/mcp")

    def enable(self):
        if not self._is_enabled:
            self._is_enabled = True
            if not self._mcp_server:
                self._mcp_server = FastMCP(self.server_name)
                
                @self._mcp_server.tool()
                def health_check() -> dict:
                    """Returns the server name and a health status."""
                    if not self._is_enabled:
                        return {"server_name": self.server_name, "status": "off", "message": "MCP server is disabled."}
                    return {"server_name": self.server_name, "status": "ok"}

                @self._mcp_server.tool()
                def collection_list() -> list[dict]:
                    """Returns a list of enabled collections with their names and descriptions."""
                    if not self._is_enabled:
                        return []
                    with get_db_connection() as db:
                        collections = get_enabled_collections_for_mcp(db)
                    return collections
                
                # Start the server thread only once when the MCP server is first initialized
                self._server_thread = threading.Thread(target=self._run_server, daemon=True)
                self._server_thread.start()
                # Give the server a moment to start
                time.sleep(1)
                print(f"MCP server '{self.server_name}' started.")

    def disable(self):
        if self._is_enabled:
            self._is_enabled = False

    def is_enabled(self) -> bool:
        return self._is_enabled



    def get_mcp_server(self) -> FastMCP | None:
        return self._mcp_server

    def add_tool(self, func):
        if self._mcp_server:
            self._mcp_server.tool()(func)
        else:
            print("MCP server not initialized, cannot add tool.")

    def add_resource(self, path: str):
        if self._mcp_server:
            return self._mcp_server.resource(path)
        else:
            print("MCP server not initialized, cannot add resource.")
            return lambda f: f # Return a no-op decorator

    def add_prompt(self, func):
        if self._mcp_server:
            self._mcp_server.prompt()(func)
        else:
            print("MCP server not initialized, cannot add prompt.")
mcp_manager = MCPManager()
