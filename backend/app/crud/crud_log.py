import uuid
from sqlite3 import Connection
from app.schemas.mcp import Message

def create_log(db: Connection, collection_id: str, collection_name: str, topic: str, message: str) -> Message:
    new_id = str(uuid.uuid4())
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO logs (id, collectionId, collectionName, topic, message) VALUES (?, ?, ?, ?, ?)",
        (new_id, collection_id, collection_name, topic, message),
    )
    db.commit()
    cursor.execute("SELECT id, timestamp, collectionId, collectionName, topic, message FROM logs WHERE id = ?", (new_id,))
    log = cursor.fetchone()
    return Message(**log)
