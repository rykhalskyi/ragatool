from app.crud import crud_log
from app.database import get_db_connection
from app.models.messages import MessageType
from app.schemas.mcp import Message
import queue
from datetime import datetime

class MessageHub:
    def __init__(self):
        self.message_queue = queue.Queue()

    def send_message(self, collection_id: str, collection_name: str, topic: MessageType, message: str):
        
        if topic == MessageType.LOG:
            db = get_db_connection()
            log_message = crud_log.create_log(db, collection_id, collection_name, message)
            db.close()
            self.message_queue.put(log_message)
        else:
            msg = Message(
                id="000",
                timestamp=datetime.now(),
                collectionId=collection_id, 
                collectionName=collection_name,
                topic=topic.name,
                message=message)
            self.message_queue.put(msg)

    def get_message(self) -> Message:
        return self.message_queue.get()

message_hub = MessageHub()
