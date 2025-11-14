import threading
import queue
import uuid
import time
import asyncio
from app.crud import crud_task

class BackgroundTaskDispatcher:
    def __init__(self, num_workers=4):
        self.task_id_queue = queue.Queue()
        self.waiting_tasks = {}
        self.running_tasks = {}
        self.lock = threading.Lock()
        self.num_workers = num_workers
        self.workers = []
        self._start_workers()

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

            task_func, args, kwargs, cancellation_event = None, None, None, None
            with self.lock:
                if task_id in self.waiting_tasks:
                    task_func, args, kwargs = self.waiting_tasks.pop(task_id)
                    cancellation_event = threading.Event()
                    self.running_tasks[task_id] = cancellation_event

            if task_func:
                try:
                    crud_task.update_task_status(task_id, "RUNNING")
                    kwargs['cancellation_event'] = cancellation_event
                    if asyncio.iscoroutinefunction(task_func):
                        asyncio.run(task_func(*args, **kwargs))
                    else:
                        task_func(*args, **kwargs)
                    crud_task.update_task_status(task_id, "COMPLETED")
                except Exception as e:
                    print(f"Task {task_id} failed: {e}")
                    crud_task.update_task_status(task_id, "FAILED")
                finally:
                    with self.lock:
                        if task_id in self.running_tasks:
                            del self.running_tasks[task_id]
                    self.task_id_queue.task_done()

    def add_task(self, collection_id: str, task_name: str, task_func, *args, **kwargs):
        task_id = str(uuid.uuid4())
        start_time = int(time.time())
        crud_task.create_task(task_id, collection_id, task_name, start_time, "NEW")
        with self.lock:
            self.waiting_tasks[task_id] = (task_func, args, kwargs)
        self.task_id_queue.put(task_id)
        return task_id

    def cancel_task(self, task_id: str):
        with self.lock:
            if task_id in self.waiting_tasks:
                del self.waiting_tasks[task_id]
                crud_task.update_task_status(task_id, "CANCELLED")
                return True
            elif task_id in self.running_tasks:
                self.running_tasks[task_id].set()
                crud_task.update_task_status(task_id, "CANCELLED")
                return True
        return False

    def stop(self):
        for _ in range(self.num_workers):
            self.task_id_queue.put(None)
        for worker in self.workers:
            worker.join()
