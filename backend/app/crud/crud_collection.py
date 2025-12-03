import chromadb
from sqlite3 import Connection, IntegrityError
from typing import List, Optional

from app.database import get_db_connection
from app.schemas.collection import Collection, CollectionCreate, ImportType, CollectionDetails
from app.schemas.imports import Import


from app.internal.exceptions import DuplicateCollectionError
from app.internal.utils import prepare_collection_name

def get_collections(db: Connection) -> List[Collection]:
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, enabled, import_type, model, settings FROM collections")
    collections = cursor.fetchall()
    return [Collection(**collection) for collection in collections]

def get_collection(db: Connection, collection_id: str) -> Optional[Collection]:
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, enabled, import_type, model, settings FROM collections WHERE id = ?", (str(collection_id),))
    collection = cursor.fetchone()
    if collection is None:
        return None
    return Collection(**collection)

def get_collection_by_name(db: Connection, collection_name: str) -> Optional[Collection]:
    cursor = db.cursor()
    # Query using the prepared name for uniqueness checks, but the name stored in DB is the original
    prepared_name_for_query = prepare_collection_name(collection_name)
    cursor.execute("SELECT id, name, description, enabled, import_type, model, settings FROM collections WHERE id = ?", (prepared_name_for_query,))
    collection = cursor.fetchone()
    if collection is None:
        return None
    return Collection(**collection)

def create_collection(db: Connection, collection: CollectionCreate) -> Collection:
    prepared_name = prepare_collection_name(collection.name)
    # Check if a collection with the prepared name already exists
    # Use a raw SQL query to check the 'name_for_query' column
    cursor_check = db.cursor()
    cursor_check.execute("SELECT COUNT(*) FROM collections WHERE id = ?", (prepared_name,))
    if cursor_check.fetchone()[0] > 0:
        raise DuplicateCollectionError()

    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO collections (id, name, description, enabled, model, settings) VALUES (?, ?, ?, ?, ?, ?)",
            (prepared_name, collection.name, collection.description, collection.enabled, collection.model, collection.settings),
        )
        db.commit()

        # Create the collection in ChromaDB
        client = chromadb.PersistentClient(path="./chroma_data")
        client.get_or_create_collection(name=prepared_name)

    except IntegrityError:
        # This catch might not be strictly necessary if the COUNT(*) check is always reliable,
        # but it's good for robustness against race conditions or unexpected DB states.
        raise DuplicateCollectionError()
    
    return Collection(id=prepared_name, **collection.model_dump())

def update_collection_description_and_enabled(db: Connection, collection_id: str, collection: CollectionCreate) -> Optional[Collection]:
    cursor = db.cursor()
    cursor.execute(
        "UPDATE collections SET description = ?, enabled = ? WHERE id = ?",
        (collection.description, collection.enabled, str(collection_id)),
    )
    db.commit()
    if cursor.rowcount == 0:
        return None
    return get_collection(db, collection_id)

import json

def update_collection_import_type(db: Connection, collection_id: str, import_params:Import):
    cursor = db.cursor()
    settings_json = json.dumps(import_params.settings.model_dump())
    cursor.execute(
        "UPDATE collections SET import_type = ?, model =?, settings = ? WHERE id = ?",
        (import_params.name, import_params.model, settings_json, str(collection_id)),
    )
    db.commit()
    return {"message": "Collection updated successfully"}
    

def update_collection_import_settings(db: Connection, collection_id: str, import_params:Import):
    cursor = db.cursor()
    settings_json = json.dumps(import_params.settings.model_dump())
    cursor.execute(
        "UPDATE collections SET settings = ? WHERE id = ?",
        (settings_json, str(collection_id)),
    )
    db.commit()
    return {"message": "Collection updated successfully"}

def delete_collection(db: Connection, collection_id: str):
    # First, get the collection to be able to return its data
    collection_to_delete = get_collection(db, collection_id)
    if collection_to_delete is None:
        return None

    cursor = db.cursor()
    cursor.execute("DELETE FROM collections WHERE id = ?", (str(collection_id),))
    db.commit()
    
    if cursor.rowcount == 0:
        # This case should ideally not be hit if get_collection found it, but for safety:
        return None
        
    return collection_to_delete

def get_collection_details(db: Connection, collection_id: str) -> Optional[CollectionDetails]:
    # Get base collection data from SQLite
    collection_base = get_collection(db, collection_id)
    if collection_base is None:
        return None

    try:
        # Connect to ChromaDB to get more details
        client = chromadb.PersistentClient(path="./chroma_data")
        chroma_collection = client.get_collection(name=collection_id)

        # Get count and metadata
        count = chroma_collection.count()
        metadata = chroma_collection.metadata

        # Create the detailed response object
        collection_details = CollectionDetails(
            **collection_base.model_dump(),
            count=count,
            metadata=metadata
        )
        return collection_details

    except Exception as e:
        # If ChromaDB fails, we can decide to return partial data or nothing.
        # For now, we'll return what we have from SQLite and mark the rest as None.
        print(f"Could not retrieve details from ChromaDB for {collection_id}: {e}")
        return CollectionDetails(**collection_base.model_dump(), count=None, metadata=None)

import json

def get_enabled_collections_for_mcp(db: Connection) -> List[dict]:
    cursor = db.cursor()
    cursor.execute("SELECT name, description, model, settings FROM collections WHERE enabled = TRUE")
    collections_data = cursor.fetchall()
    
    # Parse the settings JSON and integrate into the response
    result = []
    for col in collections_data:
        settings = json.loads(col["settings"]) if col["settings"] else {}
        result.append({
            "name": col["name"],
            "description": col["description"],
            "properties": f'text is divided to chunks of {settings.get("chunk_size")} symbols and {settings.get("chunk_overlap")} overlap'
        })
    return result

    