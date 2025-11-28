"""
This module defines custom exceptions for the RAGatouille backend.
"""

class DuplicateCollectionError(Exception):
    """
    Raised when attempting to create a collection with a name that already exists.
    """
    def __init__(self, message="A collection with this name already exists."):
        self.message = message
        super().__init__(self.message)
