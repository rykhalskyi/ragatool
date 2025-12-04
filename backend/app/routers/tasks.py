from sqlite3 import Connection
from typing import List
from fastapi import APIRouter, Depends
from app.database import get_db_connection
from app.internal.background_task_dispatcher import BackgroundTaskDispatcher
from app.dependencies import get_task_dispatcher
from app.crud import crud_task
from app.schemas import task as task_schema

router = APIRouter()

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, task_dispatcher: BackgroundTaskDispatcher = Depends(get_task_dispatcher)):
    task_dispatcher.cancel_task(task_id)
    return {"message": f"Task {task_id} cancelled"}

@router.get("/tasks", response_model=List[task_schema.Task])
def get_tasks(db: Connection = Depends(get_db_connection)):
    return crud_task.get_all_tasks(db)
