from sqlite3 import Connection
import threading
import queue
import uuid
import time
import asyncio
from app.crud import crud_task
from app.internal.message_hub import MessageHub

class BackgroundTaskDispatcher:
    def __init__(self, message_hub: MessageHub, db:Connection, num_workers=4):
        self.task_id_queue = queue.Queue()
        self.waiting_tasks = {}
        self.running_tasks = {}
        self.lock = threading.Lock()
        self.num_workers = num_workers
        self.workers = []
        self._start_workers()
        self.message_hub = message_hub
        self.db = db

    def _start_workers(self):
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self._worker_main)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def _worker_main(self):
        while True:
            task_id = self.task_id_queue.get()
            if task_id is None:
                break

            task_func, args, kwargs = None, None, None
            with self.lock:
                if task_id in self.waiting_tasks:
                    task_func, args, kwargs = self.waiting_tasks.pop(task_id)
                    cancellation_event = kwargs.get('cancel_event')
                    if cancellation_event is None:
                        cancellation_event = threading.Event()
                    self.running_tasks[task_id] = cancellation_event

            if task_func:
                try:
                    crud_task.update_task_status(self.db, task_id, "RUNNING")
                   
                    kwargs['cancel_event'] = cancellation_event
                    if asyncio.iscoroutinefunction(task_func):
                        asyncio.run(task_func(*args, **kwargs))
                    else:
                        task_func(*args, **kwargs)
                    crud_task.update_task_status(self.db, task_id, "COMPLETED")
                except Exception as e:
                    print(f"Task {task_id} failed: {e}")
                    crud_task.update_task_status(self.db, task_id, "FAILED")
                finally:
                    with self.lock:
                        if task_id in self.running_tasks:
                            del self.running_tasks[task_id]
                    self.task_id_queue.task_done()
                    crud_task.delete_task(self.db, task_id)
                    self.message_hub.send_task_message('Task deleted')

    def add_task(self, collection_id: str, task_name: str, task_func, *args, **kwargs):
        task_id = str(uuid.uuid4())
        start_time = int(time.time())
        crud_task.create_task(self.db, task_id, collection_id, task_name, start_time, "NEW")
        self.message_hub.send_task_message('Task created')
        
        with self.lock:
            new_args = (collection_id,) + args
            self.waiting_tasks[task_id] = (task_func, new_args, kwargs)
        self.task_id_queue.put(task_id)
        return task_id

    def cancel_task(self, task_id: str):
        with self.lock:
            if task_id in self.waiting_tasks:
                del self.waiting_tasks[task_id]
                crud_task.update_task_status(self.db, task_id, "CANCELLING")
                self.message_hub.send_task_message('Task cancelled')
                return True
            elif task_id in self.running_tasks:
                self.running_tasks[task_id].set()
                crud_task.update_task_status(self.db, task_id, "CANCELLING")
                self.message_hub.send_task_message('Task cancelled')
                return True
        return False

    def stop(self):
        for _ in range(self.num_workers):
            self.task_id_queue.put(None)
        for worker in self.workers:
            worker.join()
