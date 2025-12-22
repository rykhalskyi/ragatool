
from sqlite3 import Connection
from typing import List
from fastapi import APIRouter, Depends

from app.crud.crud_files import get_files_for_collection
from app.dependencies import get_db
from app.schemas.file import File


router = APIRouter()

@router.get("/{collection_id}", response_model=List[File])
def read_files(collection_id: str, db: Connection = Depends(get_db)):
    return get_files_for_collection(db, collection_id)