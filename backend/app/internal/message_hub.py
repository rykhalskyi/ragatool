from app.crud import crud_log
from app.database import get_db_connection
from app.schemas.mcp import Message
import queue

class MessageHub:
    def __init__(self):
        self.message_queue = queue.Queue()

    def send_message(self, collection_id: str, collection_name: str, topic: str, message: str):
        db = get_db_connection()
        log_message = crud_log.create_log(db, collection_id, collection_name, topic, message)
        db.close()
        self.message_queue.put(log_message)

    def get_message(self) -> Message:
        return self.message_queue.get()

message_hub = MessageHub()
