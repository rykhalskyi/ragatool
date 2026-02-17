"""
This module provides utility functions for the Rag-a-Tool backend.
"""

def prepare_collection_name(name: str) -> str:
    """
    Prepares a collection name for use in ChromaDB and for uniqueness checks.

    Args:
        name: The original name of the collection.

    Returns:
        The prepared name, converted to lowercase and with spaces replaced by underscores.
    """
        
    return name.lower().replace(' ', '_')
