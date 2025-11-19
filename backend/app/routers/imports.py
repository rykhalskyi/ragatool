import io
from fastapi import APIRouter, UploadFile, File, Depends, Form
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
    return [Import(name=file_import.name, embedding_model=file_import.embedding_model, chunk_size=file_import.chunk_size, chunk_overlap=file_import.chunk_overlap)]

@router.post("/{collection_id}")
async def import_file(collection_id: str, import_params: str = Form(...), file: UploadFile = File(...), db: Connection = Depends(get_db_connection)):
    task_name = f"Importing {file.filename} to {collection_id}"
    
    import_params_model = Import.model_validate_json(import_params)
    
    collection = crud_collection.get_collection(db, collection_id)
    if (collection == None):
        return {"message": "Collection not found."}
    
    # Read the file content into an in-memory buffer
    file_content = await file.read()
    file_buffer = io.BytesIO(file_content)
    
    # Create a new UploadFile object from the in-memory buffer
    # This is a workaround to pass the file to the background task
    # as the original file object will be closed after the request
    file_for_background = UploadFile(filename=file.filename, file=file_buffer)

    task_dispatcher.add_task(collection_id, task_name, FileImport().import_data, collection.name, file_for_background, import_params_model)
    
    if collection and collection.import_type == ImportType.NONE:
        crud_collection.update_collection_import_type(db, collection_id, import_params_model)
        
    return {"message": "File import started in the background."}
