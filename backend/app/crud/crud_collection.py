from sqlite3 import Connection
from typing import List, Optional
import uuid

from app.database import get_db_connection
from app.schemas.collection import Collection, CollectionCreate, ImportType
from app.schemas.imports import Import


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
    cursor.execute("SELECT id, name, description, enabled, import_type, model, settings FROM collections WHERE name = ?", (collection_name,))
    collection = cursor.fetchone()
    if collection is None:
        return None
    return Collection(**collection)

def create_collection(db: Connection, collection: CollectionCreate) -> Collection:
    new_id = str(uuid.uuid4())
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO collections (id, name, description, enabled, model, settings) VALUES (?, ?, ?, ?, ?, ?)",
        (new_id, collection.name, collection.description, collection.enabled, collection.model, collection.settings),
    )
    db.commit()
    return Collection(id=new_id, **collection.model_dump())

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
    cursor = db.cursor()
    cursor.execute("DELETE FROM collections WHERE id = ?", (str(collection_id),))
    db.commit()
    if cursor.rowcount == 0:
        return None
    return {"message": "Collection deleted successfully"}

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

    