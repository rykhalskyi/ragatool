from sqlite3 import Connection
import sqlite3
from typing import List
import uuid

from app.schemas.file import File


def create_file(db: Connection, collection_id: str, path: str, source: str):
    id = str(uuid.uuid4())
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO files (id, collection_id, path, source) VALUES (?, ?, ?, ?)",
        (id, collection_id, path, source),
    )
    db.commit()

def get_files_for_collection(db: Connection, collection_id: str) -> List[File]:
    db.row_factory = sqlite3.Row
    cursor = db.execute("SELECT id, timestamp, collection_id, path, source FROM files WHERE collection_id=?", (collection_id,))
    files_rows = cursor.fetchall()
    return [File(**row) for row in files_rows]

def get_file(db:Connection, file_id: str) -> File:
    db.row_factory = sqlite3.Row
    cursor = db.execute("SELECT id, timestamp, collection_id, path, source FROM files WHERE id=?", (file_id,))
    file = cursor.fetchone()
    return File(**file)

def delete_files_by_collection_id(db: Connection, collection_id: str):
    cursor = db.cursor()
    cursor.execute("DELETE FROM files WHERE collection_id = ?", (collection_id,))
    db.commit()
    if cursor.rowcount == 0:
        return None
    return {"message": "Files deleted successfully"}

def delete_file(db: Connection, id:str):
    cursor = db.cursor()
    cursor.execute("DELETE FROM files WHERE id = ?", (id,))
    db.commit()
    if cursor.rowcount == 0:
        return None
    return {"message": "Files deleted successfully"}