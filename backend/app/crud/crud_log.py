import uuid
import sqlite3
from sqlite3 import Connection
from app.models.messages import MessageType
from app.schemas.mcp import Message
from datetime import datetime

def create_log(db: Connection, collection_id: str, collection_name: str, message: str) -> Message:
    new_id = str(uuid.uuid4())
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO logs (id, collectionId, collectionName, message) VALUES (?, ?, ?, ?)",
        (new_id, collection_id, collection_name, message),
    )
    db.commit()
    return Message(id=new_id,
                   timestamp=datetime.now(),
                   collectionId=collection_id,
                   collectionName=collection_name,
                   topic=MessageType.LOG.name,
                   message=message)

def get_latest_log_entries(db: Connection, n: int):
    db.row_factory = sqlite3.Row  # Set row_factory to return dictionary-like rows
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, timestamp, collectionId, collectionName, message FROM logs ORDER BY timestamp LIMIT ?",
        (n,)
    )
    logs = cursor.fetchall()
    db.row_factory = None  # Reset row_factory to default
    
    return [Message(**log, topic=MessageType.LOG.name) for log in logs]
