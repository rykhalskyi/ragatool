from sqlite3 import Connection
import threading
import uuid
from app.crud import crud_log
from app.models.messages import MessageType
from app.schemas.mcp import Message
import queue
from datetime import datetime

class MessageHub:
    def __init__(self, db:Connection):
        self.incoming_message_queue = queue.Queue()
        self.clients = set()
        self.db = db
        self.id = uuid.uuid4()
        print('MH: create', self.id)

    def register_client(self):
        print('MH: add client')
        q = queue.Queue()
        self.clients.add(q)
        return q
    
    def unregister_client(self, q):
        print('MH: unregister client')
        self.clients.discard(q)

    def broadcast_loop(self):
        print('MH: Starting broadcast loop')
        while True:
            msg = self.incoming_message_queue.get()
            # send to all clients
            for q in list(self.clients):
                try:
                    q.put(msg)
                except:
                    pass

    def send_task_message(self, message:str):
        self.send_message("GLOBAL", MessageType.TASK, message)

    def send_message(self, collection_id: str, topic: MessageType, message: str):
        print('MH: send message', topic, message)
        if topic == MessageType.LOG:
            log_message = crud_log.create_log(self.db, collection_id, topic.name, message)
            self.incoming_message_queue.put(log_message)
        else:
            msg = Message(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                collectionId=collection_id, 
                topic=topic.name,
                message=message)
            self.incoming_message_queue.put(msg)
    def get_message(self) -> Message:
      msg = self.incoming_message_queue.get()
      print("GET popped", self.id, msg.topic, msg.message, threading.get_ident())
      return msg