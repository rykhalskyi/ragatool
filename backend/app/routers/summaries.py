from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlite3 import Connection

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

@router.post("/", response_model=str)
def create_new_summary(summary: SummaryCreate, db: Connection = Depends(get_db)):
    """
    Create a new summary.
    """
    try:
        summary_id = create_summary(db, Summary(id="", **summary.model_dump()))
        return summary_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.put("/{summary_id}")
def update_existing_summary(summary_id: str, summary: SummaryUpdate, db: Connection = Depends(get_db)):
    """
    Update an existing summary.
    """
    # First, we might want to check if it exists, but edit_summary doesn't currently return status
    # For now, we'll just call it and assume it works or raises exception
    try:
        # We need a full Summary object for edit_summary, but it only uses type, summary, metadata from it
        # and summary_id separately.
        temp_summary = Summary(id=summary_id, collection_id="", **summary.model_dump())
        edit_summary(db, summary_id, temp_summary)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.delete("/{summary_id}")
def delete_existing_summary(summary_id: str, db: Connection = Depends(get_db)):
    """
    Delete a summary.
    """
    try:
        delete_summary_by_id(db, summary_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
