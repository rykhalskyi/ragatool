from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlite3 import Connection

from app.schemas.collection import Collection, CollectionCreate
from app.crud.crud_collection import get_collections, create_collection, update_collection_description_and_enabled, delete_collection, get_collection
from app.dependencies import get_db

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
    return create_collection(db, collection)

@router.put("/{collection_id}", response_model=Collection)
def update_existing_collection(collection_id: str, collection: CollectionCreate, db: Connection = Depends(get_db)):
    updated_collection = update_collection_description_and_enabled(db, collection_id, collection)
    if updated_collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return updated_collection

@router.delete("/{collection_id}")
def delete_existing_collection(collection_id: str, db: Connection = Depends(get_db)):
    result = delete_collection(db, collection_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return result
