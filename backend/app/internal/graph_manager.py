import os
import threading
import re
from neo4j import GraphDatabase
from typing import Dict, Any, Optional, List

class GraphManager:
# ... (rest of the class remains the same until query_graph)

    def query_graph(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        Executes a read-only Cypher query and returns the results as a list of dictionaries.
        
        Args:
            cypher_query (str): The Cypher query to execute.
        """
        # 1. Basic safety check for write keywords (Case-Insensitive)
        # Using word boundaries to avoid matching keywords inside properties or strings (though not foolproof)
        forbidden_keywords = r"\b(CREATE|MERGE|DELETE|SET|REMOVE|DETACH|DROP|CALL|LOAD|PERIODIC|COMMIT)\b"
        if re.search(forbidden_keywords, cypher_query, re.IGNORECASE):
            raise ValueError("Forbidden keyword detected. Only read-only queries (MATCH...RETURN) are allowed.")

        # 2. Ensure it starts with allowed read keywords (MATCH, OPTIONAL MATCH, WITH, RETURN, UNWIND)
        # Strip leading whitespace and check start
        stripped_query = cypher_query.strip().upper()
        allowed_starts = ("MATCH", "OPTIONAL", "WITH", "RETURN", "UNWIND")
        if not stripped_query.startswith(allowed_starts):
            raise ValueError("Query must start with a read-only keyword (MATCH, WITH, RETURN, etc.).")

        self.connect()
        if not self._driver:
            raise ConnectionError("Neo4j driver not initialized.")
            
        with self._driver.session(default_access_mode="READ") as session:
            def _read_tx(tx):
                result = tx.run(cypher_query)
                return [record.data() for record in result]
            
            return session.execute_read(_read_tx)
    """
    Manages connections and operations with Neo4j graph database using environment variables directly.
    Implemented as a thread-safe Singleton.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    ALLOWED_LABELS = {"COLLECTION", "CHUNK", "PERSON", "EVENT", "PLACE", "Node", "CHAPTER"}
    ALLOWED_RELATIONS = {"CONTAINS", "MENTIONS", "LOCATED_IN", "PARTICIPATED_IN", "KNOWS"}

    def _initialize(self):
        self._driver = None
        print("INFO: GraphManager initialized (singleton pattern).")

    def _validate_label(self, label: str):
        if label not in self.ALLOWED_LABELS:
            raise ValueError(f"Label '{label}' is not allowed. Must be one of {self.ALLOWED_LABELS}")

    def _validate_relation(self, relation: str):
        if relation not in self.ALLOWED_RELATIONS:
            raise ValueError(f"Relation '{relation}' is not allowed. Must be one of {self.ALLOWED_RELATIONS}")

    def _get_credentials(self):
        # We use RAG_ prefix consistently as discussed.
        uri = os.getenv("RAG_NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("RAG_NEO4J_USER", "neo4j")
        password = os.getenv("RAG_NEO4J_PASSWORD")
        return uri, user, password


    def connect(self):
        """
        Establishes a connection to the Neo4j database if not already connected.
        """
        if self._driver is None:
            uri, user, password = self._get_credentials()
            self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """
        Closes the connection to the Neo4j database.
        """
        if self._driver:
            self._driver.close()
            self._driver = None

    def create_node(self, node_type: str, attributes: Dict[str, Any]):
        """
        Creates (or merges) a node in the graph database.

        Args:
            node_type (str): The label of the node (e.g., 'PERSON').
            attributes (dict): The properties of the node.
        """
        self._validate_label(node_type)
        self.connect()
        with self._driver.session() as session:
            # Using MERGE for idempotency as per architectural recommendations
            query = f"MERGE (n:{node_type} {{id: $props.id}}) SET n += $props RETURN n"
            # Ensure id is in attributes for MERGE to be effective as an identity
            if 'id' not in attributes:
                raise ValueError("Node attributes must include 'id' for merging.")
            session.run(query, props=attributes) # type: ignore

    def create_edge(self, src_id: str, dst_id: str, relation: str, src_label: str = "Node", dst_label: str = "Node"):
        """
        Creates (or merges) an edge between two nodes matched by their 'id' attribute.

        Args:
            src_id (str): The 'id' of the source node.
            dst_id (str): The 'id' of the destination node.
            relation (str): The type of the relationship (e.g., 'MENTIONS').
            src_label (str): The label of the source node. Defaults to 'Node'.
            dst_label (str): The label of the destination node. Defaults to 'Node'.
        """
        self._validate_label(src_label)
        self._validate_label(dst_label)
        self._validate_relation(relation)
        self.connect()
        with self._driver.session() as session:
            # Using MERGE for idempotency
            query = (
                f"MATCH (a:{src_label} {{id: $src_id}}), (b:{dst_label} {{id: $dst_id}}) "
                f"MERGE (a)-[r:{relation}]->(b) "
                f"RETURN r"
            )
            session.run(query, src_id=src_id, dst_id=dst_id)

    def add_collection(self, collection_id: str, name: str):
        """
        Adds a COLLECTION node to the graph.
        """
        self.create_node("COLLECTION", {"id": collection_id, "name": name})

    def add_chunk(self, chunk_id: str, collection_id: str, text: str, index: int):
        """
        Adds a CHUNK node and links it to its COLLECTION.
        """
        self.create_node("CHUNK", {"id": chunk_id, "text": text[:1000], "index": index}) # Truncate text for graph storage
        self.create_edge(collection_id, chunk_id, "CONTAINS", src_label="COLLECTION", dst_label="CHUNK")

    def add_chapter(self, chapter_name:str, collection_id:str, summary:str, index:int):
        """
        Add CHAPTER node and links it to its COLLECTION.
        """
        id = f"{chapter_name}_{index}"
        self.create_node("CHAPTER", {"id":id, "name":chapter_name, "summary":summary, "index":index})
        self.create_edge(collection_id, id, "CONTAINS", src_label="COLLECTION", dst_label="CHAPTER")

    def create_chapter_with_chunks(self, collection_id: str, chapter_name: str, first_chunk_id: Optional[str] = None, last_chunk_id: Optional[str] = None):
        """
        Creates a CHAPTER node, links it to a COLLECTION, and optionally links it to a range of CHUNK nodes.
        
        Args:
            collection_id (str): The ID of the parent COLLECTION.
            chapter_name (str): The name of the chapter.
            first_chunk_id (str, optional): The ID of the first chunk in the range.
            last_chunk_id (str, optional): The ID of the last chunk in the range.
        """
        # Generate chapter ID: collection_id_chapter_name slugified
        chapter_slug = chapter_name.lower().replace(" ", "_")
        chapter_id = f"{collection_id}_{chapter_slug}"
        
        # Create CHAPTER node and link to COLLECTION
        self.create_node("CHAPTER", {"id": chapter_id, "name": chapter_name})
        self.create_edge(collection_id, chapter_id, "CONTAINS", src_label="COLLECTION", dst_label="CHAPTER")
        
        # Link to chunks if range provided
        if first_chunk_id and last_chunk_id:
            try:
                # Expected format: filename_timestamp_index
                # e.g., mobydick.txt_1774648463_2165
                
                # Split and find the last underscore which separates the index
                base1, index1_str = first_chunk_id.rsplit("_", 1)
                base2, index2_str = last_chunk_id.rsplit("_", 1)
                
                if base1 != base2:
                    raise ValueError(f"Chunk ID bases do not match: '{base1}' vs '{base2}'")
                
                index1 = int(index1_str)
                index2 = int(index2_str)
                
                # Ensure range is valid
                start = min(index1, index2)
                end = max(index1, index2)
                
                chunk_ids = [f"{base1}_{i}" for i in range(start, end + 1)]
                
                self.connect()
                with self._driver.session() as session:
                    # Link CHAPTER to all CHUNKs in the list that exist in the graph
                    query = (
                        "MATCH (ch:CHAPTER {id: $chapter_id}), (c:CHUNK) "
                        "WHERE c.id IN $chunk_ids "
                        "MERGE (ch)-[:CONTAINS]->(c)"
                    )
                    session.run(query, chapter_id=chapter_id, chunk_ids=chunk_ids)
                    
            except (ValueError, IndexError) as e:
                # Log error or re-raise if chunk ID parsing fails
                print(f"ERROR: Failed to link chunks to chapter: {e}")
                raise

    def delete_collection(self, collection_id: str):
        """
        Deletes the COLLECTION node and all nodes (like CHUNKs and CHAPTERs) associated with it,
        along with all their relationships (DETACH DELETE).
        """
        self.connect()
        if self._driver:
            with self._driver.session() as session:
                # Query to find the collection and all contained nodes, then delete them all
                query = (
                    "MATCH (c:COLLECTION {id: $collection_id}) "
                    "OPTIONAL MATCH (c)-[:CONTAINS]->(n) "
                    "DETACH DELETE c, n"
                )
                session.run(query, collection_id=collection_id)
