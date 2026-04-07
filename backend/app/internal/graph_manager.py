import os
from neo4j import GraphDatabase
from typing import Dict, Any, Optional

class GraphManager:
    """
    Manages connections and operations with Neo4j graph database using environment variables directly.
    """

    def __init__(self):
        self._driver = None

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
        Creates a node in the graph database.

        Args:
            node_type (str): The label of the node (e.g., 'Person').
            attributes (dict): The properties of the node.
        """
        self.connect()
        with self._driver.session() as session:
            query = f"CREATE (n:{node_type} $props) RETURN n"
            session.run(query, props=attributes)

    def create_edge(self, src_id: str, dst_id: str, relation: str, src_label: str = "Node", dst_label: str = "Node"):
        """
        Creates an edge between two nodes matched by their 'id' attribute.

        Args:
            src_id (str): The 'id' of the source node.
            dst_id (str): The 'id' of the destination node.
            relation (str): The type of the relationship (e.g., 'FOLLOWS').
            src_label (str): The label of the source node. Defaults to 'Node'.
            dst_label (str): The label of the destination node. Defaults to 'Node'.
        """
        self.connect()
        with self._driver.session() as session:
            query = (
                f"MATCH (a:{src_label} {{id: $src_id}}), (b:{dst_label} {{id: $dst_id}}) "
                f"CREATE (a)-[r:{relation}]->(b) "
                f"RETURN r"
            )
            session.run(query, src_id=src_id, dst_id=dst_id)
