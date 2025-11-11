import unittest
from unittest.mock import patch, MagicMock
import time
import threading
from app.internal.background_task_dispatcher import BackgroundTaskDispatcher

# A dummy task that can be cancelled
def cancellable_dummy_task(duration, cancel_event: threading.Event, *args, **kwargs):
    start_time = time.time()
    while (time.time() - start_time) < duration:
        if cancel_event.is_set():
            # Task was cancelled
            return "cancelled"
        time.sleep(0.01)
    return "completed"

class TestBackgroundTaskDispatcher(unittest.TestCase):
    def test_enqueue_task(self):
        with patch('app.internal.background_task_dispatcher.crud_task') as mock_crud_task:
            dispatcher = BackgroundTaskDispatcher(num_workers=1)
            
            collection_id = "test_collection"
            task_name = "test_task"
            
            task_id = dispatcher.enqueue_task(collection_id, task_name, cancellable_dummy_task, 0.1, cancel_event=threading.Event())
            
            self.assertIsNotNone(task_id)
            mock_crud_task.create_task.assert_called_once()
            
            # Give the worker time to process the task
            time.sleep(0.2) # Increased sleep to ensure task completes
            
            mock_crud_task.update_task_status.assert_any_call(task_id, "RUNNING")
            mock_crud_task.update_task_status.assert_any_call(task_id, "COMPLETED")
            
            dispatcher.stop()

    def test_cancel_queued_task(self):
        with patch('app.internal.background_task_dispatcher.crud_task') as mock_crud_task:
            dispatcher = BackgroundTaskDispatcher(num_workers=1)
            
            collection_id = "test_collection"
            task_name = "test_task_queued"
            
            # Enqueue a long-running task first to ensure the next one stays in queue
            long_task_id = dispatcher.enqueue_task(collection_id, "long_task", cancellable_dummy_task, 10, cancel_event=threading.Event())
            
            # Enqueue the task to be cancelled
            task_id_to_cancel = dispatcher.enqueue_task(collection_id, task_name, cancellable_dummy_task, 0.1, cancel_event=threading.Event())
            
            # Immediately cancel the second task
            self.assertTrue(dispatcher.cancel_task(task_id_to_cancel))
            
            # Assert that the task status was updated to CANCELLED
            mock_crud_task.update_task_status.assert_called_with(task_id_to_cancel, "CANCELLED")
            
            # Assert that the task is no longer in waiting_tasks
            with dispatcher.lock:
                self.assertNotIn(task_id_to_cancel, dispatcher.waiting_tasks)
            
            # Clean up the long running task
            dispatcher.cancel_task(long_task_id)
            dispatcher.stop()

    def test_cancel_running_task(self):
        with patch('app.internal.background_task_dispatcher.crud_task') as mock_crud_task:
            dispatcher = BackgroundTaskDispatcher(num_workers=1)
            
            collection_id = "test_collection"
            task_name = "test_task_running"
            
            # Enqueue a task that runs for a while
            task_id = dispatcher.enqueue_task(collection_id, task_name, cancellable_dummy_task, 1, cancel_event=threading.Event())
            
            # Wait for the task to start running
            time.sleep(0.1) 
            
            # Assert that it's marked as running
            mock_crud_task.update_task_status.assert_any_call(task_id, "RUNNING")
            
            # Cancel the running task
            self.assertTrue(dispatcher.cancel_task(task_id))
            
            # Assert that the task status was updated to CANCELLED
            mock_crud_task.update_task_status.assert_called_with(task_id, "CANCELLED")
            
            # Give the task some time to acknowledge the cancellation
            time.sleep(0.1)
            
            # Assert that the task is no longer in running_tasks
            with dispatcher.lock:
                self.assertNotIn(task_id, dispatcher.running_tasks)
            
            dispatcher.stop()

if __name__ == '__main__':
    unittest.main()
