from sqlite3 import Connection
from functools import lru_cache
from fastapi import Depends
from .database import get_db_connection
from app.internal.message_hub import MessageHub
from .internal.background_task_dispatcher import BackgroundTaskDispatcher
from app.internal.settings_manager import SettingsManager

_message_hub_instance: MessageHub | None = None
_task_dispatcher_instance: BackgroundTaskDispatcher | None = None

def get_db():
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()

def get_message_hub_instance() -> MessageHub:
    global _message_hub_instance
    if _message_hub_instance is None:
        _message_hub_instance = MessageHub(get_db_connection())
    return _message_hub_instance

def get_task_dispatcher_instance() -> BackgroundTaskDispatcher:
    global _task_dispatcher_instance
    if _task_dispatcher_instance is None:
        _task_dispatcher_instance = BackgroundTaskDispatcher(get_message_hub_instance(), get_db_connection())
    return _task_dispatcher_instance

def get_task_dispatcher():
    yield get_task_dispatcher_instance()

def get_message_hub():
    yield get_message_hub_instance()

@lru_cache()
def get_settings_manager(db: Connection = Depends(get_db)) -> SettingsManager:
    return SettingsManager(db)