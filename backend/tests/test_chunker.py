import pytest
from app.internal.chunker import Chunker, ChunkType

@pytest.fixture
def chunker():
    return Chunker()

def test_create_chunks_default(chunker):
    text = "This is a test text for chunking."
    chunks = chunker.create_chunks(text, ChunkType.DEFAULT, 10, 2)
    assert len(chunks) > 0
    assert chunks[0] == "This is a "
    assert chunks[1] == "a test tex"

def test_create_chunks_recursive_character(chunker):
    text = "This is a test text for chunking."
    chunks = chunker.create_chunks(text, ChunkType.RECURSIVE_CHARACTER, 10, 2)
    assert len(chunks) > 0
    assert chunks[0] == "This is a"
    assert chunks[1] == "a test"

def test_create_chunks_empty_text(chunker):
    text = ""
    chunks = chunker.create_chunks(text, ChunkType.DEFAULT, 10, 2)
    assert len(chunks) == 0

def test_create_chunks_no_overlap(chunker):
    text = "This is a test text for chunking."
    chunks = chunker.create_chunks(text, ChunkType.DEFAULT, 10, 0)
    assert len(chunks) > 0
    assert chunks[0] == "This is a "
    assert chunks[1] == "test text "
