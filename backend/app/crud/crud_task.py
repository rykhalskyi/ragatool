import sqlite3
from sqlite3 import Connection
from typing import List
from app.schemas.task import Task

def create_task(db: Connection, task_id: str, collection_id: str, name: str, start_time: int, status: str):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO tasks (id, collectionId, name, startTime, status) VALUES (?, ?, ?, ?, ?)",
        (task_id, collection_id, name, start_time, status),
    )
    db.commit()


def get_task(db: Connection, task_id: str):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    return task

def update_task_status(db: Connection, task_id: str, status: str):
    cursor = db.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    db.commit()


def delete_task(db: Connection, task_id: str):
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()


def get_all_tasks(db: Connection) -> List[Task]:
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("SELECT id, collectionId, name, startTime, status FROM tasks")
    tasks = cursor.fetchall()

    return [Task(**task) for task in tasks ]

def delete_all_tasks(db: Connection):
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks")
    db.commit()