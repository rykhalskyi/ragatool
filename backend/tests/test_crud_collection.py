import pytest
import sqlite3
from sqlite3 import Connection
from app.crud import crud_collection
from app.schemas.collection import Collection, CollectionCreate, ImportType
from app.schemas.imports import Import, FileImportSettings
from app.database import create_tables
import uuid

@pytest.fixture
def db_connection():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_tables(conn)
    yield conn
    conn.close()

    # Tests will go here

def test_create_collection(db_connection):
    collection_data = CollectionCreate(
        name="Test Collection",
        description="A collection for testing",
        enabled=True,
        model="some_model",
        settings="{}"
    )
    collection = crud_collection.create_collection(db_connection, collection_data)
    assert collection.name == "Test Collection"
    assert collection.description == "A collection for testing"
    assert collection.enabled is True
    assert collection.model == "some_model"
    assert collection.settings == "{}"
    assert isinstance(collection.id, uuid.UUID)

def test_get_collection(db_connection):
    collection_data = CollectionCreate(
        name="Test Collection 2",
        description="Another collection for testing",
        enabled=False,
        model="another_model",
        settings="{}"
    )
    created_collection = crud_collection.create_collection(db_connection, collection_data)
    retrieved_collection = crud_collection.get_collection(db_connection, created_collection.id)
    assert retrieved_collection == created_collection

def test_get_collection_by_name(db_connection):
    collection_data = CollectionCreate(
        name="Test Collection 3",
        description="Yet another collection for testing",
        enabled=True,
        model="yet_another_model",
        settings="{}"
    )
    created_collection = crud_collection.create_collection(db_connection, collection_data)
    retrieved_collection = crud_collection.get_collection_by_name(db_connection, "Test Collection 3")
    assert retrieved_collection == created_collection

def test_get_collections(db_connection):
    crud_collection.create_collection(db_connection, CollectionCreate(name="Col1", description="Desc1", enabled=True, model="m1", settings="{}"))
    crud_collection.create_collection(db_connection, CollectionCreate(name="Col2", description="Desc2", enabled=False, model="m2", settings="{}"))
    collections = crud_collection.get_collections(db_connection)
    assert len(collections) == 2  # Only 2 collections created in this test
    assert any(col.name == "Col1" for col in collections)
    assert any(col.name == "Col2" for col in collections)

def test_update_collection_description_and_enabled(db_connection):
    collection_data = CollectionCreate(
        name="Test Collection 4",
        description="Original description",
        enabled=False,
        model="model_to_update",
        settings="{}"
    )
    created_collection = crud_collection.create_collection(db_connection, collection_data)
    
    updated_data = CollectionCreate(
        name="Test Collection 4", # Name should not change
        description="Updated description",
        enabled=True,
        model="model_to_update",
        settings="{}"
    )
    updated_collection = crud_collection.update_collection_description_and_enabled(db_connection, created_collection.id, updated_data)
    assert updated_collection.description == "Updated description"
    assert updated_collection.enabled is True
    assert updated_collection.name == created_collection.name # Ensure name is unchanged

def test_update_collection_import_type(db_connection):
    collection_data = CollectionCreate(
        name="Test Collection 5",
        description="Collection for import type update",
        enabled=True,
        model="initial_model",
        settings="{}"
    )
    created_collection = crud_collection.create_collection(db_connection, collection_data)

    import_params = Import(
        name=ImportType.FILE,
        model="new_model_for_api",
        settings=FileImportSettings(chunk_size=100, chunk_overlap=20, no_chunks=False)
    )
    result = crud_collection.update_collection_import_type(db_connection, created_collection.id, import_params)
    assert result == {"message": "Collection updated successfully"}

    updated_collection = crud_collection.get_collection(db_connection, created_collection.id)
    assert updated_collection.import_type == ImportType.FILE
    assert updated_collection.model == "new_model_for_api"
    # Convert string settings back to dict to check content
    import json
    settings = json.loads(updated_collection.settings)
    assert settings["chunk_size"] == 100
    assert settings["chunk_overlap"] == 20

def test_update_collection_import_settings(db_connection):
    collection_data = CollectionCreate(
        name="Test Collection 6",
        description="Collection for import settings update",
        enabled=True,
        model="model_for_settings",
        settings='{"chunk_size": 50, "chunk_overlap": 10}'
    )
    created_collection = crud_collection.create_collection(db_connection, collection_data)

    import_params = Import(
        name=ImportType.NONE, # Type and model should not change via this function
        model="model_for_settings",
        settings=FileImportSettings(chunk_size=200, chunk_overlap=50, no_chunks=False)
    )
    result = crud_collection.update_collection_import_settings(db_connection, created_collection.id, import_params)
    assert result == {"message": "Collection updated successfully"}

    updated_collection = crud_collection.get_collection(db_connection, created_collection.id)
    # Ensure only settings are updated
    assert updated_collection.import_type == ImportType.NONE # Should remain NONE from initial creation
    assert updated_collection.model == "model_for_settings"
    import json
    settings = json.loads(updated_collection.settings)
    assert settings["chunk_size"] == 200
    assert settings["chunk_overlap"] == 50

def test_delete_collection(db_connection):
    collection_data = CollectionCreate(
        name="Test Collection 7",
        description="Collection to be deleted",
        enabled=True,
        model="model_to_delete",
        settings="{}"
    )
    created_collection = crud_collection.create_collection(db_connection, collection_data)
    result = crud_collection.delete_collection(db_connection, created_collection.id)
    assert result == {"message": "Collection deleted successfully"}
    deleted_collection = crud_collection.get_collection(db_connection, created_collection.id)
    assert deleted_collection is None

def test_delete_non_existent_collection(db_connection):
    result = crud_collection.delete_collection(db_connection, str(uuid.uuid4()))
    assert result is None

def test_get_enabled_collections_for_mcp(db_connection):
    # Create an enabled collection with settings
    collection_data_enabled = CollectionCreate(
        name="MCP Enabled Collection",
        description="This is an enabled collection for MCP",
        enabled=True,
        model="mcp_model_1",
        settings='{"chunk_size": 256, "chunk_overlap": 30}'
    )
    crud_collection.create_collection(db_connection, collection_data_enabled)

    # Create a disabled collection
    collection_data_disabled = CollectionCreate(
        name="MCP Disabled Collection",
        description="This is a disabled collection for MCP",
        enabled=False,
        model="mcp_model_2",
        settings='{"chunk_size": 128, "chunk_overlap": 15}'
    )
    crud_collection.create_collection(db_connection, collection_data_disabled)

    enabled_collections = crud_collection.get_enabled_collections_for_mcp(db_connection)

    assert len(enabled_collections) == 1
    mcp_collection = enabled_collections[0]

    assert mcp_collection["name"] == "MCP Enabled Collection"
    assert mcp_collection["description"] == "This is an enabled collection for MCP"
    assert mcp_collection["properties"] == "text is divided to chunks of 256 symbols and 30 overlap"








