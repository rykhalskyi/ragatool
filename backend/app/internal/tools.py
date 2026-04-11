import chromadb
from typing import List
import asyncio
import time
import json
from app.crud.crud_collection_content import query_collection as crud_query_collection
from app.database import get_db_connection
from app.crud.crud_collection import get_enabled_collections_for_mcp, get_collection_by_name, create_collection
from app.internal.extension_manager import ExtensionManager
from app.schemas.mcp import ExtensionTool
from app.schemas.collection import CollectionCreate
from app.internal.embedding_manager import get_embedder
from app.crud.crud_summary import get_summary_by_id, get_summary_by_type, create_summary, edit_summary, delete_summary_by_id
from app.schemas.summary import SummaryType, Summary
from app.internal.graph_manager import GraphManager

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
    def add_fact(fact: str, summary: str) -> dict:
        """
        Saves a fact about the user for long-term memory.
        - fact: The full text of the fact to remember.
        - summary: A brief summary of the fact, used for search embeddings.
        """
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}

        collection_name = "agent_ltm"
        return add_to_collection(collection_name, fact, summary)
        

    @mcp_server.tool()
    def add_to_collection(collection_name:str, fact: str, summary: str) -> dict:
        """
        Adds a fact to a given collection.
        - collection_name: The name of collection to save fact
        - fact: The full text of the fact to remember.
        - summary: A brief summary of the fact, used for search embeddings.
        """
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            with get_db_connection() as db:
                collection_meta = get_collection_by_name(db, collection_name)
                if not collection_meta:
                    # Create it if it doesn't exist
                    create_collection(db, CollectionCreate(
                        name=collection_name,
                        description="Long Term Memory for AI Agent facts about the user",
                        enabled=True
                    ))
            
            client = chromadb.PersistentClient(path="./chroma_data")
            collection = client.get_collection(name=collection_name)
            
            embedder = get_embedder()
            embedding = list(embedder.embed([summary]))[0].tolist()
            
            ts = int(time.time())
            fact_id = f"fact_{ts}"
            
            collection.add(
                documents=[fact],
                embeddings=[embedding],
                metadatas=[{"summary": summary, "ts": ts}],
                ids=[fact_id]
            )
            
            return {"status": "success", "message": f"Fact saved to {collection_name}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

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
        - ids: a single ID (string), a list of IDs (list[str]), or a JSON string representation of a list
        """
        collection_name = collection_name.lower().replace(' ','_')

        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}

        try:
            # Normalize IDs into a list
            if isinstance(ids, str):
                ids_stripped = ids.strip()
                # Check if it's a JSON string representation of a list
                if ids_stripped.startswith('[') and ids_stripped.endswith(']'):
                    try:
                        parsed = json.loads(ids_stripped)
                        if isinstance(parsed, list):
                            ids = [str(i) for i in parsed]
                        else:
                            ids = [ids]
                    except json.JSONDecodeError:
                        ids = [ids]
                else:
                    ids = [ids]
            elif isinstance(ids, list):
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
        
    ## Summary

    @mcp_server.tool()
    def get_table_of_contents(collection_name: str):
        """
        Retrieves TOC for the collection
        - collection_name: name of the ChromaDB collection
        """

        collection_id = prepare_collection_name(collection_name)

        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        with get_db_connection() as db:
            toc_list = get_summary_by_type(db, collection_id, SummaryType.TOC)
            if len(toc_list) > 0:
                return {"status": "success", "toc": toc_list[0].model_dump()}
            else:
                return {"status": "error", "message": f"No table of contents found for collection '{collection_name}'."}

    @mcp_server.tool()
    def add_table_of_contents(collection_name: str, toc: str):
        """
        Add TOC for the collection
        - collection_name: name of the ChromaDB collection
        - toc: table of contents in string (must contain chunk ids)
        """

        collection_id = prepare_collection_name(collection_name)

        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        new_toc = Summary(id="", collection_id=collection_id, type=SummaryType.TOC, summary=toc)
        with get_db_connection() as db:
            toc_old = get_summary_by_type(db, collection_id, SummaryType.TOC)
            if len(toc_old) > 0:
                edit_summary(db, toc_old[0].id, new_toc)
            else:
                create_summary(db, new_toc)
            return {"status": "success"}
        
    
    @mcp_server.tool()
    def update_table_of_contents(collection_name: str, toc: str):
        """
        Updates TOC for the collection
        - collection_name: name of the ChromaDB collection
        - toc: table of contents in string (must contain chunk ids)
        """

        collection_id = prepare_collection_name(collection_name)

        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        new_toc = Summary(id="", collection_id=collection_id, type=SummaryType.TOC, summary=toc)
        with get_db_connection() as db:
            toc_list = get_summary_by_type(db, collection_id, SummaryType.TOC)
            if len(toc_list) > 0:
                edit_summary(db, toc_list[0].id, new_toc)
                return {"status": "success"}
            else:
                return {"status": "error", "message": f"No table of contents found for collection '{collection_name}'."}

    @mcp_server.tool()
    def get_summaries(collection_name: str, summary_type: int):
        """
        Retrieves all summaries by type from a collection
        - collection_name: name of the ChromaDB collection
        - summary_type: type of summary (0: CHUNKS, 1: CHAPTER, 2: BOOK)
        """
        collection_id = prepare_collection_name(collection_name)
        
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            summary_type_enum = SummaryType(summary_type)
        except ValueError:
            return {"status": "error", "message": f"Invalid summary type. Must be 0-2 (CHUNKS, CHAPTER, BOOK)."}
        
        with get_db_connection() as db:
            summaries = get_summary_by_type(db, collection_id, summary_type_enum)
            if len(summaries) > 0:
                return {"status": "success", "summaries": [s.model_dump() for s in summaries]}
            else:
                return {"status": "error", "message": f"No summaries found for type {summary_type_enum.name} in collection '{collection_name}'."}

    @mcp_server.tool()
    def get_single_summary(collection_name: str, summary_type: int, summary_index:int):
        """
        Retrieves single summary by type from a collection
        - collection_name: name of the ChromaDB collection
        - summary_type: type of summary (0: CHUNKS, 1: CHAPTER, 2: BOOK)
        - summary_index: index of a summary in the list
        """
        collection_id = prepare_collection_name(collection_name)
        
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            summary_type_enum = SummaryType(summary_type)
        except ValueError:
            return {"status": "error", "message": f"Invalid summary type. Must be 0-2 (CHUNKS, CHAPTER, BOOK)."}
        
        with get_db_connection() as db:
            summaries = get_summary_by_type(db, collection_id, summary_type_enum)
            if len(summaries) > 0:
                if summary_index <= len(summaries) - 1: 
                    return {"status": "success", "summary": summaries[summary_index].model_dump}
                else: return {"status": "error", "message": f"Index out of range {len(summaries)-1}"}
            else:
                return {"status": "error", "message": f"No summaries found for type {summary_type_enum.name} in collection '{collection_name}'."}

    @mcp_server.tool()
    def add_summary(collection_name: str, summary_type: int, summary_text: str, metadata: str | None = None):
        """
        Adds a summary to a collection
        - collection_name: name of the ChromaDB collection
        - summary_type: type of summary (0: CHUNKS, 1: CHAPTER, 2: BOOK)
        - summary_text: the summary content. must contain chunk or lower summaries ids
        - metadata: optional metadata for the summary
        """
        collection_id = prepare_collection_name(collection_name)
        
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            summary_type_enum = SummaryType(summary_type)
        except ValueError:
            return {"status": "error", "message": f"Invalid summary type. Must be 0-2 (CHUNKS, CHAPTER, BOOK)."}
        
        try:
            new_summary = Summary(id="", collection_id=collection_id, type=summary_type_enum, summary=summary_text, metadata=metadata)
            with get_db_connection() as db:
                summary_id = create_summary(db, new_summary)
                return {"status": "success", "summary_id": summary_id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp_server.tool()
    def update_summary(summary_id: str, summary_type: int, summary_text: str, collection_name: str, metadata: str | None = None):
        """
        Updates an existing summary
        - summary_id: the ID of the summary to update
        - summary_type: type of summary (0: CHUNKS, 1: CHAPTER, 2: BOOK)
        - summary_text: the new summary content. must contain chunk or lower summaries ids
        - collection_name: name of the ChromaDB collection
        - metadata: optional metadata for the summary
        """
        collection_id = prepare_collection_name(collection_name)
        
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            summary_type_enum = SummaryType(summary_type)
        except ValueError:
            return {"status": "error", "message": f"Invalid summary type. Must be 0-2 (CHUNKS, CHAPTER, BOOK)."}
        
        try:
            updated_summary = Summary(id=summary_id, collection_id=collection_id, type=summary_type_enum, summary=summary_text, metadata=metadata)
            with get_db_connection() as db:
                edit_summary(db, summary_id, updated_summary)
                return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp_server.tool()
    def delete_summary(summary_id: str):
        """
        Delete an existing summary
        - summary_id: the ID of the summary to update
        """
        
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        try:
            with get_db_connection() as db:
                delete_summary_by_id(db, summary_id)
            return {"status": "success", "message": "Summary deleted."}
        except Exception as e:       
            return {"status": "error", "message": str(e)} 

    @mcp_server.tool()
    def graph_add_entities(chunk_id: str, entities: str) -> dict:
        """
        Adds multiple entities (PERSON, PLACE, EVENT) found in a specific chunk to the graph.
        - chunk_id: The ID of the chunk where entities were found.
        - entities: A JSON list of objects: [{"type": "PERSON"|"PLACE"|"EVENT", "name": "Dracula", "description": "The vampire count"}]
        """
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            entity_list = json.loads(entities)
            gm = GraphManager()
            for entity in entity_list:
                e_type = entity.get("type")
                e_name = entity.get("name")
                e_desc = entity.get("description", "")
                
                if not e_type or not e_name:
                    continue
                
                # Use name as id for entities for simplicity and entity resolution via MERGE
                entity_id = e_name.strip().lower().replace(" ", "_")
                
                # Create entity node
                gm.create_node(e_type, {"id": entity_id, "name": e_name, "description": e_desc})
                # Link CHUNK -[:MENTIONS]-> ENTITY
                gm.create_edge(chunk_id, entity_id, "MENTIONS", src_label="CHUNK", dst_label=e_type)
            
            return {"status": "success", "message": f"Added {len(entity_list)} entities to chunk {chunk_id}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp_server.tool()
    def graph_link_entities(source_name: str, source_type: str, target_name: str, target_type: str, relation: str) -> dict:
        """
        Creates a relationship between two entities in the graph.
        - source_name: Name of the source entity (e.g. Dracula).
        - source_type: Type of the source entity (PERSON, PLACE, EVENT).
        - target_name: Name of the target entity (e.g. Transylvania).
        - target_type: Type of the target entity (PERSON, PLACE, EVENT).
        - relation: Type of relationship (LOCATED_IN, PARTICIPATED_IN, KNOWS).
        """
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            gm = GraphManager()
            src_id = source_name.strip().lower().replace(" ", "_")
            dst_id = target_name.strip().lower().replace(" ", "_")
            
            gm.create_edge(src_id, dst_id, relation, src_label=source_type, dst_label=target_type)
            return {"status": "success", "message": f"Linked {source_name} to {target_name} via {relation}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp_server.tool()
    def graph_create_chapter(collection_id: str, chapter_name: str, first_chunk_id: str | None = None, last_chunk_id: str | None = None) -> dict:
        """
        Creates a chapter node in the graph and links it to a collection and chunks.
        - collection_id: The ID of the collection the chapter belongs to.
        - chapter_name: The name of the chapter.
        - first_chunk_id: The ID of the first chunk in the range (optional).
        - last_chunk_id: The ID of the last chunk in the range (optional).
        """
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            gm = GraphManager()
            gm.create_chapter_with_chunks(collection_id, chapter_name, first_chunk_id, last_chunk_id)
            msg = f"Chapter '{chapter_name}' created and linked to collection '{collection_id}'"
            if first_chunk_id and last_chunk_id:
                msg += f" and chunks from {first_chunk_id} to {last_chunk_id}."
            else:
                msg += "."
            return {"status": "success", "message": msg}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp_server.tool()
    def graph_query(query: str) -> dict:
        """
        Executes a read-only Cypher query against the Neo4j graph.
        - query: The Cypher query (e.g., 'MATCH (n:CHAPTER) RETURN n.name').
        Use this to explore relationships between collections, chapters, and chunks.
        Only MATCH and RETURN operations are allowed.
        """
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            gm = GraphManager()
            results = gm.query_graph(query)
            return {
                "status": "success",
                "results": results,
                "count": len(results)
            }
        except ValueError as e:
            return {"status": "error", "message": f"Security validation failed: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Query execution failed: {str(e)}"}

    @mcp_server.tool()
    def get_wiki_index(collection_id: str):
        """
        Returns index of wiki pages for collection.
        The index contains summary's title, type, tags, and ID.
        """
        collection_id = prepare_collection_name(collection_id)
        
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        with get_db_connection() as db:
            summaries = get_summary_by_type(db, collection_id, SummaryType.WIKI)
            if len(summaries) > 0:
                wiki_index = []
                for s in summaries:
                    # Extract metadata fields
                    meta = {}
                    if s.metadata:
                        try:
                            meta = json.loads(s.metadata)
                        except json.JSONDecodeError:
                            pass
                    
                    wiki_index.append({
                        "id": s.id,
                        "title": meta.get("title", ""),
                        "type": meta.get("type", ""),
                        "tags": meta.get("tags", [])
                    })
                return {"status": "success", "wiki index": wiki_index}
            else:
                return {"status": "error", "message": f"No wiki pages found in collection '{collection_id}'."}

    @mcp_server.tool()
    def add_wiki_page(collection_id: str, page_title: str, type: str, tags: List[str], text: str) -> dict:
        """
        Adds a wiki page to a collection.
        - collection_id: id of the collection.
        - page_title: title of the wiki page. IMPORTANT!
        - type: category/type of the wiki page (e.g. Character, Location, Plot).
        - tags: list of tags for the wiki page.
        - text: the content of the wiki page.
        """
        #print("Add wiki called: ", page_title)
        collection_id = prepare_collection_name(collection_id)
        
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            metadata = json.dumps({"title": page_title, "type": type, "tags": tags})
            new_wiki = Summary(id="", collection_id=collection_id, type=SummaryType.WIKI, summary=text, metadata=metadata)
            with get_db_connection() as db:
                summary = create_summary(db, new_wiki)
                return {"status": "success", "message": "Wiki page added.", "page_id": summary.id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp_server.tool()
    def edit_wiki_page(page_id: str, page_title: str, type: str, tags: List[str], text: str) -> dict:
        """
        Edits an existing wiki page.
        - page_id: the ID of the wiki page to edit.
        - page_title: new title.
        - type: new category/type.
        - tags: new list of tags.
        - text: new content.
        """
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            with get_db_connection() as db:
                existing = get_summary_by_id(db, page_id)
                if not existing or existing.type != SummaryType.WIKI:
                    return {"status": "error", "message": f"Wiki page with ID {page_id} not found."}
                
                metadata = json.dumps({"title": page_title, "type": type, "tags": tags})
                updated_wiki = Summary(id=page_id, collection_id=existing.collection_id, type=SummaryType.WIKI, summary=text, metadata=metadata)
                edit_summary(db, page_id, updated_wiki)
                return {"status": "success", "message": "Wiki page updated."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @mcp_server.tool()
    def get_wiki_page(page_id: str) -> dict:
        """
        Retrieves a wiki page by ID.
        - page_id: the ID of the wiki page.
        """
        if not mcp_manager.is_enabled():
            return {"status": "error", "message": "MCP server is disabled."}
        
        try:
            with get_db_connection() as db:
                summary = get_summary_by_id(db, page_id)
                if not summary or summary.type != SummaryType.WIKI:
                    return {"status": "error", "message": f"Wiki page with ID {page_id} not found."}
                
                meta = {}
                if summary.metadata:
                    try:
                        meta = json.loads(summary.metadata)
                    except json.JSONDecodeError:
                        pass
                
                result = {
                    "id": summary.id,
                    "collection_id": summary.collection_id,
                    "title": meta.get("title", ""),
                    "type": meta.get("type", ""),
                    "tags": meta.get("tags", []),
                    "text": summary.summary
                }
                return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def prepare_collection_name(collection_name: str) -> str:
        return collection_name.lower().replace(' ','_')        
    