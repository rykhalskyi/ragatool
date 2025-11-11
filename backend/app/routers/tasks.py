from fastapi import APIRouter, Depends
from app.internal.background_task_dispatcher import BackgroundTaskDispatcher
from app.dependencies import get_task_dispatcher

router = APIRouter()

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, task_dispatcher: BackgroundTaskDispatcher = Depends(get_task_dispatcher)):
    task_dispatcher.cancel_task(task_id)
    return {"message": f"Task {task_id} cancelled"}
