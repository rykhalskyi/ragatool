from fastmcp import FastMCP
import threading
import time
import os
from app.internal.tools import register_tools


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
        self._sse_server: FastMCP | None = None
        self._http_server: FastMCP | None = None
        self._is_enabled: bool = False
        self._sse_thread: threading.Thread | None = None
        self._http_thread: threading.Thread | None = None
        self.server_name = "Rag-a-Tool"

    def _run_sse_server(self):
        if self._sse_server:
            # FastMCP.run() is a blocking call, so it needs to be in a separate thread
            host = os.getenv("MCP_HOST", "127.0.0.1")
            port = int(os.getenv("MCP_PORT", 8001))
            self._sse_server.run(transport="sse", host=host, port=port, path="/mcp")
    
    def _run_http_server(self):
        """Run HTTP server for opencode"""
        if self._http_server:
            host = os.getenv("MCP_HTTP_HOST", "127.0.0.1")
            port = int(os.getenv("MCP_HTTP_PORT", 8002))
            self._http_server.run(transport="http", host=host, port=port, path="/mcp")

    def enable(self):
        if not self._is_enabled:
            self._is_enabled = True
            if not self._sse_server:
                self._sse_server = FastMCP(f"{self.server_name}-SSE")
                self._http_server = FastMCP(f"{self.server_name}-HTTP")

                register_tools(self._sse_server, self)
                register_tools(self._http_server, self)

                # Start SSE server (for other agents)
                self._sse_thread = threading.Thread(
                    target=self._run_sse_server, daemon=True
                )
                self._sse_thread.start()
                
                # Start HTTP server (for opencode)
                self._http_thread = threading.Thread(
                    target=self._run_http_server, daemon=True
                )
                self._http_thread.start()

                # Give the server a moment to start
                time.sleep(1)
                print(f"MCP server '{self.server_name}' started.")
                print(f"  SSE: http://127.0.0.1:8001/mcp")
                print(f"  HTTP: http://127.0.0.1:8002/mcp")

    def disable(self):
        if self._is_enabled:
            self._is_enabled = False

    def is_enabled(self) -> bool:
        return self._is_enabled



    def get_mcp_server(self) -> FastMCP | None:
        return self._sse_server

    def add_tool(self, func):
        if self._sse_server:
            self._sse_server.tool()(func)
        else:
            print("MCP server not initialized, cannot add tool.")

    def add_resource(self, path: str):
        if self._sse_server:
            return self._sse_server.resource(path)
        else:
            print("MCP server not initialized, cannot add resource.")
            return lambda f: f # Return a no-op decorator

    def add_prompt(self, func):
        if self._sse_server:
            self._sse_server.prompt()(func)
        else:
            print("MCP server not initialized, cannot add prompt.")
mcp_manager = MCPManager()
