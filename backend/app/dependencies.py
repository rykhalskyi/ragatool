from .database import get_db_connection
from .internal.background_task_dispatcher import BackgroundTaskDispatcher

task_dispatcher = BackgroundTaskDispatcher()

def get_db():
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()

def get_task_dispatcher():
    yield task_dispatcher
