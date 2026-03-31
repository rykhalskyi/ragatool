import pytest
import sqlite3
import tempfile
from unittest.mock import patch
import chromadb

from app.database import create_tables
from app.crud import crud_summary
from app.schemas.summary import Summary, SummaryType

@pytest.fixture
def db_connection():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('chromadb.PersistentClient') as mock_persistent_client:
            mock_persistent_client.return_value = chromadb.PersistentClient(path=tmpdir)
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            create_tables(conn)
            yield conn
            conn.close()

def test_create_summary(db_connection):
    summary_data = Summary(
        id="",
        collection_id="test_collection",
        type=SummaryType.TOC,
        summary="Test TOC content",
        metadata="test metadata"
    )
    new_summary = crud_summary.create_summary(db_connection, summary_data)
    assert new_summary is not None
    assert isinstance(new_summary.id, str)

    summaries = crud_summary.get_summaries(db_connection, "test_collection")
    assert len(summaries) == 1
    assert summaries[0].summary == "Test TOC content"
    assert summaries[0].collection_id == "test_collection"
    assert summaries[0].type == SummaryType.TOC
    assert summaries[0].metadata == "test metadata"

def test_get_summary_by_type(db_connection):
    # Create multiple summaries
    crud_summary.create_summary(db_connection, Summary(id="", collection_id="col1", type=SummaryType.TOC, summary="TOC 1"))
    crud_summary.create_summary(db_connection, Summary(id="", collection_id="col1", type=SummaryType.CHAPTER, summary="CHAPTER 1"))
    crud_summary.create_summary(db_connection, Summary(id="", collection_id="col1", type=SummaryType.CHAPTER, summary="CHAPTER 2"))
    crud_summary.create_summary(db_connection, Summary(id="", collection_id="col1", type=SummaryType.BOOK, summary="BOOK 1"))
    crud_summary.create_summary(db_connection, Summary(id="", collection_id="col2", type=SummaryType.TOC, summary="TOC 2"))

    col1_toc = crud_summary.get_summary_by_type(db_connection, "col1", SummaryType.TOC)
    assert len(col1_toc) == 1
    assert col1_toc[0].summary == "TOC 1"
    
    col1_chapter = crud_summary.get_summary_by_type(db_connection, "col1", SummaryType.CHAPTER)
    assert len(col1_chapter) == 2
    assert col1_chapter[0].summary == "CHAPTER 1"
    assert col1_chapter[1].summary == "CHAPTER 2"
    
    col1_book = crud_summary.get_summary_by_type(db_connection, "col1", SummaryType.BOOK)
    assert len(col1_book) == 1
    assert col1_book[0].summary == "BOOK 1"

    col2_toc = crud_summary.get_summary_by_type(db_connection, "col2", SummaryType.TOC)
    assert len(col2_toc) == 1
    assert col2_toc[0].summary == "TOC 2"

def test_edit_summary(db_connection):
    summary_data = Summary(id="", collection_id="col1", type=SummaryType.TOC, summary="Old summary")
    new_summary = crud_summary.create_summary(db_connection, summary_data)

    updated_summary = Summary(id=new_summary.id, collection_id="col1", type=SummaryType.TOC, summary="New summary", metadata="new metadata")
    crud_summary.edit_summary(db_connection, new_summary.id, updated_summary)

    summaries = crud_summary.get_summaries(db_connection, "col1")
    assert len(summaries) == 1
    assert summaries[0].summary == "New summary"
    assert summaries[0].metadata == "new metadata"

def test_delete_summary(db_connection):
    new_summary = crud_summary.create_summary(db_connection, Summary(id="", collection_id="col1", type=SummaryType.TOC, summary="To delete"))
    assert len(crud_summary.get_summaries(db_connection, "col1")) == 1

    crud_summary.delete_summary_by_id(db_connection, new_summary.id)
    assert len(crud_summary.get_summaries(db_connection, "col1")) == 0

def test_delete_all_summaries_for_collection(db_connection):
    crud_summary.create_summary(db_connection, Summary(id="", collection_id="col1", type=SummaryType.TOC, summary="TOC"))
    crud_summary.create_summary(db_connection, Summary(id="", collection_id="col1", type=SummaryType.BOOK, summary="BOOK"))
    crud_summary.create_summary(db_connection, Summary(id="", collection_id="col2", type=SummaryType.TOC, summary="OTHER"))

    assert len(crud_summary.get_summaries(db_connection, "col1")) == 2
    crud_summary.delete_all_summaries_for_collection(db_connection, "col1")
    assert len(crud_summary.get_summaries(db_connection, "col1")) == 0
    assert len(crud_summary.get_summaries(db_connection, "col2")) == 1
