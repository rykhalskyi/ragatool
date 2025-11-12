from fastapi import APIRouter, UploadFile, File, Depends
from typing import List
from sqlite3 import Connection
from app.models.imports import FileImport
from app.internal.background_task_dispatcher import BackgroundTaskDispatcher
from app.crud import crud_collection
from app.database import get_db_connection
from app.schemas.collection import ImportType
from app.schemas.imports import Import

router = APIRouter()
task_dispatcher = BackgroundTaskDispatcher()

@router.get("/")
def get_imports() -> List[Import]:
    file_import = FileImport()
    return [Import(name=file_import.name, embedding_model=file_import.embedding_model, chunk_size=file_import.chunk_size, chunk_overlay=file_import.chunk_overlay)]

@router.post("/{collection_name}")
async def import_file(collection_id: str, file: UploadFile = File(...), db: Connection = Depends(get_db_connection)):
    task_name = f"Importing {file.filename} to {collection_id}"
    
    collection = crud_collection.get_collection(db, collection_id)
    if (collection == None):
        return {"message": "Collection not found."}
    
    task_dispatcher.add_task(collection_id, task_name, FileImport().import_data, collection.name, file)
    
    if collection and collection.import_type == ImportType.NONE:
        crud_collection.update_collection_import_type(db, collection_id, ImportType.FILE)
        
    return {"message": "File import started in the background."}
