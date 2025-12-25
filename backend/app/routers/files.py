
from sqlite3 import Connection
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.crud.crud_files import get_file, get_files_for_collection
from app.dependencies import get_db
from app.internal.temp_file_helper import TempFileHelper
from app.models.imports import FileImport
from app.schemas.file import File, ChunkPreviewRequest, ChunkPreviewResponse


router = APIRouter()

@router.get("/{collection_id}", response_model=List[File])
def read_files(collection_id: str, db: Connection = Depends(get_db)):
    return get_files_for_collection(db, collection_id)

@router.post("/content", response_model=ChunkPreviewResponse)
def get_chunk_preview(request: ChunkPreviewRequest, db: Connection = Depends(get_db)):
    try:
        filename = get_file(db, request.file_id)
        content = TempFileHelper.get_temp_file_content(filename.path)
        
        importer = FileImport()
        all_chunks = []
        if not request.no_chunks:
            all_chunks = importer.create_chunks(content, request.chunk_size, request.chunk_overlap)
        else:
            all_chunks = [content]
            
        start_index = request.skip_number
        end_index = start_index + request.take_number
        
        paginated_chunks = all_chunks[start_index:end_index]
        
        more_chunks = end_index < len(all_chunks)
        
        return ChunkPreviewResponse(chunks=paginated_chunks, more_chunks=more_chunks)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Temporary file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")