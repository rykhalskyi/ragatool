import asyncio
import io
import threading
from unittest.mock import MagicMock, patch
import pytest
from fastapi import UploadFile
from app.routers.imports import import_file
from app.models.imports import FileImport

@pytest.mark.asyncio
async def test_import_file_background_task():
    # 1. Mock the database connection and CRUD operations
    mock_db = MagicMock()
    mock_crud_collection = MagicMock()
    mock_crud_collection.get_collection.return_value = MagicMock(id="test_collection", name="test_collection", import_type="NONE")

    # 2. Create a mock file
    file_content = b"This is a test file."
    file_buffer = io.BytesIO(file_content)
    mock_file = UploadFile(filename="test.txt", file=file_buffer)

    # 3. Mock the BackgroundTaskDispatcher
    mock_task_dispatcher = MagicMock()

    # 4. Patch the dependencies
    with patch("app.routers.imports.get_db_connection", return_value=mock_db), \
         patch("app.routers.imports.crud_collection", mock_crud_collection), \
         patch("app.routers.imports.task_dispatcher", mock_task_dispatcher):

        # 5. Call the endpoint function
        response = await import_file(
            collection_id="test_collection",
            import_params='{"name": "FILE", "embedding_model": "all-MiniLM-L6-v2", "chunk_size": 300, "chunk_overlap": 50}',
            file=mock_file,
            db=mock_db
        )

        # 6. Assert that the background task was added
        mock_task_dispatcher.add_task.assert_called_once()
        
        # 7. Get the arguments passed to the background task
        args = mock_task_dispatcher.add_task.call_args[0]
        
        # 8. The actual file object is the 4th argument
        background_file = args[4]
        
        # 9. Simulate the background task by calling the import_data method
        importer = FileImport()
        cancellation_event = threading.Event()
        
        # This call would have raised the "I/O operation on closed file" error
        # with the old code.
        await importer.import_data(
            collection_name="test_collection",
            file=background_file,
            cancellation_event=cancellation_event
        )
        
        # 10. Assert that the file was read correctly
        # (This is an indirect way to check that no error was raised)
        assert not cancellation_event.is_set()
        
        # 11. Check the response
        assert response == {"message": "File import started in the background."}