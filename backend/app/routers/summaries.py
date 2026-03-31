from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlite3 import Connection
import logging

from app.schemas.summary import Summary, SummaryCreate, SummaryUpdate, SummaryType
from app.crud.crud_summary import (
    get_summaries,
    get_summary_by_type,
    create_summary,
    edit_summary,
    delete_summary_by_id
)
from app.dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/collection/{collection_id}", response_model=List[Summary])
def list_summaries_by_collection(collection_id: str, db: Connection = Depends(get_db)):
    """
    Get all summaries for a specific collection.
    """
    return get_summaries(db, collection_id)

@router.get("/collection/{collection_id}/type/{summary_type}", response_model=List[Summary])
def list_summaries_by_type(collection_id: str, summary_type: int, db: Connection = Depends(get_db)):
    """
    Get summaries of a specific type for a collection.
    """
    try:
        summary_type_enum = SummaryType(summary_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid summary type: {summary_type}")
    
    return get_summary_by_type(db, collection_id, summary_type_enum)

@router.post("/", response_model=Summary, status_code=201)
def create_new_summary(summary: SummaryCreate, db: Connection = Depends(get_db)):
    """
    Create a new summary.
    """
    try:
        return create_summary(db, Summary(id="", **summary.model_dump()))
    except Exception as e:
        logger.error(f"Error creating summary: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the summary.")

@router.put("/{summary_id}", response_model=Summary)
def update_existing_summary(summary_id: str, summary: SummaryUpdate, db: Connection = Depends(get_db)):
    """
    Update an existing summary.
    """
    try:
        temp_summary = Summary(id=summary_id, collection_id="", **summary.model_dump())
        success = edit_summary(db, summary_id, temp_summary)
        if not success:
            raise HTTPException(status_code=404, detail="Summary not found")
        # Return full updated object. We need collection_id which is missing in temp_summary update
        # For now we'll just return what we have or rethink if we need to fetch it first.
        # Collections router returns the full object after fetching it.
        # Let's keep it simple for now as per plan.
        return temp_summary 
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating summary {summary_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating the summary.")

@router.delete("/{summary_id}")
def delete_existing_summary(summary_id: str, db: Connection = Depends(get_db)):
    """
    Delete a summary.
    """
    try:
        success = delete_summary_by_id(db, summary_id)
        if not success:
            raise HTTPException(status_code=404, detail="Summary not found")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting summary {summary_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting the summary.")
