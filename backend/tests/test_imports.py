import asyncio
import io
import threading
from unittest.mock import MagicMock, patch
import pytest
from fastapi import UploadFile
from app.routers.imports import import_file
from app.models.imports import FileImport
from app.database import create_tables # New import

@pytest.mark.asyncio
async def test_import_file_background_task():
    create_tables() # Call create_tables at the beginning of the test

    # 1. Mock the database connection and CRUD operations
    mock_db = MagicMock()
    mock_crud_collection = MagicMock()
    mock_collection_instance = MagicMock(id="test_collection_id", import_type="NONE")
    mock_collection_instance.name = "test_collection_name"
    mock_crud_collection.get_collection.return_value = mock_collection_instance

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
        
        # The arguments passed to import_data are now:
        # collection_id (args[0])
        # collection_name (args[3])
        # file (args[4])
        # cancel_event (kwargs['cancel_event'])

        # 9. Simulate the background task by calling the import_data method
        importer = FileImport()
        cancellation_event = threading.Event()
        
        await importer.import_data(
            collection_id=args[0], # Pass collection_id
            collection_name=args[3], # Pass collection_name
            file=args[4], # Pass file
            cancel_event=cancellation_event
        )
        
        # 10. Assert that the file was read correctly
        # (This is an indirect way to check that no error was raised)
        assert not cancellation_event.is_set()
        
        # 11. Check the response
        assert response == {"message": "File import started in the background."}