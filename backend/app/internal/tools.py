import chromadb
from typing import List
import asyncio
from app.crud.crud_collection_content import query_collection as crud_query_collection
from app.database import get_db_connection
from app.crud.crud_collection import get_enabled_collections_for_mcp
from app.internal.extension_manager import ExtensionManager
from app.schemas.mcp import ExtensionTool

def register_tools(mcp_server, mcp_manager):
    """
    Registers all the tools for the MCP server.
    """

    @mcp_server.tool()
    def health_check() -> dict:
        """Returns the server name and a health status."""
        if not mcp_manager.is_enabled():
            return {"server_name": mcp_manager.server_name, "status": "off", "message": "MCP server is disabled."}
        return {"server_name": mcp_manager.server_name, "status": "ok"}

    @mcp_server.tool()
    def collection_list() -> list[dict]:
        """Returns a list of enabled collections with their names and descriptions."""
        if not mcp_manager.is_enabled():
            return []
        with get_db_connection() as db:
            collections = get_enabled_collections_for_mcp(db)
        return collections

    @mcp_server.tool()
    def extension_list() -> List[dict]:
        """Returns a list of all connected extensions and their supported commands."""
        if not mcp_manager.is_enabled():
            return []
        
        manager = ExtensionManager()
        extension_tools = manager.get_registered_extension_tools()
        
        # Convert Pydantic models to dictionaries
        return [tool.model_dump() for tool in extension_tools]

    @mcp_server.tool()
    async def call_extension(id: str, name: str, input: str) -> dict:
        """
        Calls a command on a connected extension.
        - id: The ID of the extension to call.
        - name: The name of the command to invoke.
        - input: A dictionary with the input parameters for the command.
        """
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}

        if not id or not name or input is None:
            return {"status": "error", "message": "Missing required parameters: id, name, or input."}

        manager = ExtensionManager()
        try:
            response = await manager.send_command_and_wait_for_response(id, name, input, timeout=10)
            return response
        except ConnectionError as e:
            return {"status": "error", "message": str(e)}
        except asyncio.TimeoutError:
            return {"status": "error", "message": f"Command '{name}' on extension '{id}' timed out after 10 seconds."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp_server.tool()
    def query_collection(collection_name: str, query_text: str, n_results: int = 10) -> dict:
        """
        Queries a collection with a given text.
        - collection_name: The name of the collection to query.
        - query_text: The text to query the collection with.
        - n_results: The number of results to return.
        """
        collection_name = collection_name.lower().replace(' ','_')
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        try:
            return crud_query_collection(collection_name, query_text, n_results)
        except ValueError as e:
            return {
                "status": "error",
                "message": f"Collection '{collection_name}' not found. {str(e)}",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp_server.tool()
    def get_chunks_by_id(collection_name: str, ids):
        """
        Retrieves one or multiple chunks from a ChromaDB collection using IDs.

        - collection_name: name of the ChromaDB collection
        - ids: a single ID (string) or a list of IDs (list[str])
        """
        collection_name = collection_name.lower().replace(' ','_')

        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}

        try:
            # Normalize IDs into a list
            if isinstance(ids, str):
                ids = [ids]
            elif isinstance(ids, list):
                # Ensure all elements are strings
                ids = [str(i) for i in ids]
            else:
                return {
                    "status": "error",
                    "message": "Parameter 'ids' must be a string or list of strings.",
                }

            client = chromadb.PersistentClient(path="./chroma_data")
            collection = client.get_collection(name=collection_name)

            results = collection.get(
                ids=ids,
                include=["documents", "metadatas"]
            )

            return {"status": "success", "results": results}

        except ValueError:
            return {
                "status": "error",
                "message": f"Collection '{collection_name}' not found.",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
