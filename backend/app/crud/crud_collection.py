from sqlite3 import Connection
from typing import List, Optional
import uuid

from app.schemas.collection import Collection, CollectionCreate


def get_collections(db: Connection) -> List[Collection]:
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, model, chunk_size, chunk_overlap, enabled FROM collections")
    collections = cursor.fetchall()
    return [Collection(**collection) for collection in collections]

def get_collection(db: Connection, collection_id: str) -> Optional[Collection]:
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, model, chunk_size, chunk_overlap, enabled FROM collections WHERE id = ?", (collection_id,))
    collection = cursor.fetchone()
    if collection is None:
        return None
    return Collection(**collection)

def create_collection(db: Connection, collection: CollectionCreate) -> Collection:
    new_id = str(uuid.uuid4())
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO collections (id, name, description, model, chunk_size, chunk_overlap, enabled) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (new_id, collection.name, collection.description, collection.model, collection.chunk_size, collection.chunk_overlap, collection.enabled),
    )
    db.commit()
    return Collection(id=new_id, **collection.model_dump())

def update_collection(db: Connection, collection_id: str, collection: CollectionCreate) -> Optional[Collection]:
    cursor = db.cursor()
    cursor.execute(
        "UPDATE collections SET description = ?, model = ?, chunk_size = ?, chunk_overlap = ?, enabled = ? WHERE id = ?",
        (collection.description, collection.model, collection.chunk_size, collection.chunk_overlap, collection.enabled, collection_id),
    )
    db.commit()
    if cursor.rowcount == 0:
        return None
    return Collection(id=collection_id, **collection.model_dump())

def delete_collection(db: Connection, collection_id: str):
    cursor = db.cursor()
    cursor.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
    db.commit()
    if cursor.rowcount == 0:
        return None
    return {"message": "Collection deleted successfully"}
