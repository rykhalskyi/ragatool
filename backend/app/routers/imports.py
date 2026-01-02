import io
from fastapi import APIRouter, UploadFile, File, Depends, Form
from typing import List
from sqlite3 import Connection

from fastapi.responses import JSONResponse
from app.crud.crud_setting import get_settings
from app.dependencies import get_message_hub, get_task_dispatcher
from app.internal.message_hub import MessageHub
from app.models.import_context import ImportContext
from app.models.imports import FileImport
from app.internal.background_task_dispatcher import BackgroundTaskDispatcher
from app.crud import crud_collection
from app.database import get_db_connection
from app.models.url_import import UrlImport
from app.schemas.collection import ImportType
from app.schemas.imports import Import
from app.schemas.setting import SettingsName
from app.internal.chunker import ChunkType

router = APIRouter()

@router.get("/")
def get_imports() -> List[Import]:
    return [FileImport.getDefault(), UrlImport.getDefault()]

@router.get("/chunktypes/")
def get_chunk_types() -> List[str]:
    return [e.value for e in ChunkType]

@router.post("/{collection_id}")
async def import_file(collection_id: str, import_params: str = Form(...), file: UploadFile = File(...), db: Connection = Depends(get_db_connection), task_dispatcher = Depends(get_task_dispatcher), message_hub:MessageHub = Depends(get_message_hub)):
    try:
        task_name = f"Importing {file.filename} to {collection_id}"
        import_params_model = Import.model_validate_json(import_params)

        import_context = ImportContext(db, message_hub, import_params_model)
        
        collection = crud_collection.get_collection(db, collection_id)
        if (collection == None):
            return {"message": "Collection not found."}
        
        # Read the file content into bytes
        file_content_bytes = await file.read()
        message_hub.send_task_message('START IMPORT')

        task_dispatcher.add_task(collection_id, task_name, FileImport().import_data, file.filename, file_content_bytes, import_context)
        
        if collection and collection.import_type == ImportType.NONE:
            crud_collection.update_collection_import_type(db, collection_id, import_params_model)
        elif collection.import_type != ImportType.NONE:
            crud_collection.update_collection_import_settings(db, collection_id, import_params_model)
            
        return {"message": "File import started in the background."}
    except Exception as e:
        return JSONResponse(
        status_code=500,
        content={"message": str(e)}
    )


@router.post("/url/{colletion_id}")
async def import_url(collection_id: str,  url: str, import_params: str = Form(...), db: Connection = Depends(get_db_connection), task_dispatcher = Depends(get_task_dispatcher), message_hub:MessageHub = Depends(get_message_hub)):
    try:
        task_name = f"Importing {url} to {collection_id}"
     
        import_params_model = Import.model_validate_json(import_params)
        
        import_context = ImportContext(db, message_hub, import_params_model)
        
        collection = crud_collection.get_collection(db, collection_id)
        if (collection == None):
            return {"message": "Collection not found."}
        
        message_hub.send_task_message('START IMPORT')

        task_dispatcher.add_task(collection_id, task_name, UrlImport().import_data, url, [], import_context)
        
        if collection and collection.import_type == ImportType.NONE:
            crud_collection.update_collection_import_type(db, collection_id, import_params_model)
        elif collection.import_type != ImportType.NONE:
            crud_collection.update_collection_import_settings(db, collection_id, import_params_model)
            
        return {"message": "Url import started in the background."}
    except Exception as e:
        return JSONResponse(
        status_code=500,
        content={"message": str(e)}
    )

@router.post("/step1/{collection_id}")
async def import_file_step_1(collection_id: str, import_params: str = Form(...), file: UploadFile = File(...), db: Connection = Depends(get_db_connection), task_dispatcher = Depends(get_task_dispatcher), message_hub:MessageHub = Depends(get_message_hub)):
    try:
        
        task_name = f"Importing {file.filename} to {collection_id} step 1"
        import_params_model = Import.model_validate_json(import_params)

        import_context = ImportContext(db, message_hub, import_params_model)

        if not import_context.settings.check(SettingsName.TWO_STEP_IMPORT, 'True'):
            return {"message": "This methid is available in 2 Step mode"}

        collection = crud_collection.get_collection(db, collection_id)
        if (collection == None):
            return {"message": "Collection not found."}
        
        # Read the file content into bytes
        file_content_bytes = await file.read()
        message_hub.send_task_message('START IMPORT')
        
        task_dispatcher.add_task(collection_id, task_name, FileImport().step_1, file.filename, file_content_bytes, import_context)
        
        if collection and collection.import_type == ImportType.NONE:
            crud_collection.update_collection_import_type(db, collection_id, import_params_model)
        elif collection.import_type != ImportType.NONE:
            crud_collection.update_collection_import_settings(db, collection_id, import_params_model)

    except Exception as e:
        return JSONResponse(
        status_code=500,
        content={"message": str(e)}) 
    
@router.post("/step2/{collection_id}")
async def import_file_step_2(collection_id: str, import_files_ids: List[str], import_params: str = Form(...),  db: Connection = Depends(get_db_connection), task_dispatcher = Depends(get_task_dispatcher), message_hub:MessageHub = Depends(get_message_hub)):
    try:
        
        task_name = f"Importing to {collection_id} step 2"
        import_params_model = Import.model_validate_json(import_params)

        import_context = ImportContext(db, message_hub, import_params_model)

        if not import_context.settings.check(SettingsName.TWO_STEP_IMPORT, 'True'):
            return {"message": "This methid is available in 2 Step mode"}        

        collection = crud_collection.get_collection(db, collection_id)
        if (collection == None):
            return {"message": "Collection not found."}
               
        task_dispatcher.add_task(collection_id, task_name, FileImport().step_2, import_context, import_files_ids)
        
        if collection and collection.import_type == ImportType.NONE:
            crud_collection.update_collection_import_type(db, collection_id, import_params_model)
        elif collection.import_type != ImportType.NONE:
            crud_collection.update_collection_import_settings(db, collection_id, import_params_model)

    except Exception as e:
        return JSONResponse(
        status_code=500,
        content={"message": str(e)}) 
    

@router.post("/url/step1/{collection_id}")
async def import_url_step_1(collection_id: str, url:str, import_params: str = Form(...), db: Connection = Depends(get_db_connection), task_dispatcher = Depends(get_task_dispatcher), message_hub:MessageHub = Depends(get_message_hub)):
    try:
        
        task_name = f"Importing {url} to {collection_id} step 1"
        import_params_model = Import.model_validate_json(import_params)

        import_context = ImportContext(db, message_hub, import_params_model)

        if not import_context.settings.check(SettingsName.TWO_STEP_IMPORT, 'True'):
            return {"message": "This method is available in 2 Step mode"}

        collection = crud_collection.get_collection(db, collection_id)
        if (collection == None):
            return {"message": "Collection not found."}
        
        message_hub.send_task_message('START IMPORT')
        
        task_dispatcher.add_task(collection_id, task_name, UrlImport().step_1, url, import_context)
        
        if collection and collection.import_type == ImportType.NONE:
            crud_collection.update_collection_import_type(db, collection_id, import_params_model)
        elif collection.import_type != ImportType.NONE:
            crud_collection.update_collection_import_settings(db, collection_id, import_params_model)

    except Exception as e:
        return JSONResponse(
        status_code=500,
        content={"message": str(e)}) 
    
    