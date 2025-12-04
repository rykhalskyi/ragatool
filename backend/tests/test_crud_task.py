import pytest
import sqlite3
from sqlite3 import Connection
from app.crud import crud_task
from app.schemas.task import Task
from app.database import create_tables
import uuid
import time

@pytest.fixture
def db_connection():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_tables(conn)
    yield conn
    conn.close()

def test_create_task(db_connection):
    task_id = str(uuid.uuid4())
    crud_task.create_task(db_connection, task_id, "collection1", "Task 1", int(time.time()), "pending")
    
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    
    assert task is not None
    assert task["id"] == task_id
    assert task["collectionId"] == "collection1"
    assert task["name"] == "Task 1"
    assert task["status"] == "pending"

def test_get_task(db_connection):
    task_id = str(uuid.uuid4())
    crud_task.create_task(db_connection, task_id, "collection1", "Task 1", int(time.time()), "pending")
    
    retrieved_task = crud_task.get_task(db_connection, task_id)
    
    assert retrieved_task is not None
    assert retrieved_task["id"] == task_id

def test_update_task_status(db_connection):
    task_id = str(uuid.uuid4())
    crud_task.create_task(db_connection, task_id, "collection1", "Task 1", int(time.time()), "pending")
    
    crud_task.update_task_status(db_connection, task_id, "completed")
    
    updated_task = crud_task.get_task(db_connection, task_id)
    assert updated_task["status"] == "completed"

def test_delete_task(db_connection):
    task_id = str(uuid.uuid4())
    crud_task.create_task(db_connection, task_id, "collection1", "Task 1", int(time.time()), "pending")
    
    crud_task.delete_task(db_connection, task_id)
    
    deleted_task = crud_task.get_task(db_connection, task_id)
    assert deleted_task is None

def test_get_all_tasks(db_connection):
    crud_task.create_task(db_connection, str(uuid.uuid4()), "collectionA", "Task A", int(time.time()), "running")
    crud_task.create_task(db_connection, str(uuid.uuid4()), "collectionB", "Task B", int(time.time()), "completed")
    
    all_tasks = crud_task.get_all_tasks(db_connection)
    
    assert len(all_tasks) == 2
    assert any(task.name == "Task A" for task in all_tasks)
    assert any(task.name == "Task B" for task in all_tasks)

def test_delete_all_tasks(db_connection):
    crud_task.create_task(db_connection, str(uuid.uuid4()), "collectionX", "Task X", int(time.time()), "running")
    crud_task.create_task(db_connection, str(uuid.uuid4()), "collectionY", "Task Y", int(time.time()), "completed")
    
    crud_task.delete_all_tasks(db_connection)
    
    all_tasks = crud_task.get_all_tasks(db_connection)
    assert len(all_tasks) == 0