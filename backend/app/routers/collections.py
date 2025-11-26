import chromadb
import os
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlite3 import Connection

from app.crud.crud_log import delete_log_by_collection_id
from app.schemas.collection import Collection, CollectionCreate
from app.crud.crud_collection import get_collections, create_collection, update_collection_description_and_enabled, delete_collection, get_collection
from app.dependencies import get_db
from app.internal.exceptions import DuplicateCollectionError
from app.internal.utils import prepare_collection_name
from app.internal.mcp_manager import mcp_manager

router = APIRouter()

@router.get("/", response_model=List[Collection])
def read_collections(db: Connection = Depends(get_db)):
    return get_collections(db)

@router.get("/{collection_id}", response_model=Collection)
def read_collection(collection_id: str, db: Connection = Depends(get_db)):
    db_collection = get_collection(db, collection_id=collection_id)
    if db_collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return db_collection

@router.post("/", response_model=Collection)
def create_new_collection(collection: CollectionCreate, db: Connection = Depends(get_db)):
    try:
        return create_collection(db, collection)
    except DuplicateCollectionError:
        raise HTTPException(status_code=409, detail="A collection with this name already exists.")

@router.put("/{collection_id}", response_model=Collection)
def update_existing_collection(collection_id: str, collection: CollectionCreate, db: Connection = Depends(get_db)):
    updated_collection = update_collection_description_and_enabled(db, collection_id, collection)
    if updated_collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return updated_collection

@router.delete("/{collection_id}")
def delete_existing_collection(collection_id: str, db: Connection = Depends(get_db)):
    deleted_collection = delete_collection(db, collection_id)
    if deleted_collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    delete_log_by_collection_id(db, collection_id)

    try:
        client = chromadb.PersistentClient(path="./chroma_data")
        # Use the prepared name for ChromaDB deletion
        chroma_collection_name = prepare_collection_name(deleted_collection.name)
        client.delete_collection(name=chroma_collection_name)
    except Exception as e:
        # It's better to log the error and decide if this should be a critical failure
        print(f"Error deleting collection '{deleted_collection.name}' from ChromaDB: {e}")
        # Depending on requirements, you might not want to raise an HTTP exception
        # if the primary DB record was successfully deleted.
        # For now, let's keep it to signal a problem.
        raise HTTPException(status_code=500, detail=f"Failed to delete collection from vector store: {e}")
        
    return deleted_collection
