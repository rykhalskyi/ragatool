import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import UploadFile
from app.models.imports import FileImport
import io
import asyncio
from fastapi.testclient import TestClient
from app.main import app

class TestFileImport(unittest.TestCase):

    @patch('app.models.imports.SentenceTransformer')
    @patch('app.models.imports.chromadb.PersistentClient')
    def test_import_data(self, mock_chromadb_client, mock_sentence_transformer):
        async def run_test():
            # Arrange
            mock_model = MagicMock()
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            mock_sentence_transformer.return_value = mock_model

            mock_collection = MagicMock()
            mock_client = MagicMock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chromadb_client.return_value = mock_client

            file_content = b"This is a test file."
            file = UploadFile(filename="test.txt", file=io.BytesIO(file_content))
            file.read = AsyncMock(return_value=file_content)
            
            file_import = FileImport()

            # Act
            await file_import.import_data("test_collection", file)

            # Assert
            mock_sentence_transformer.assert_called_once_with("all-MiniLM-L6-v2", trust_remote_code=True)
            mock_model.encode.assert_called_once()
            mock_chromadb_client.assert_called_once_with(path="./chroma_data")
            mock_client.get_or_create_collection.assert_called_once_with(name="test_collection")
            mock_collection.upsert.assert_called_once()
        
        asyncio.run(run_test())

class TestImportRoutes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('app.routers.imports.task_dispatcher')
    @patch('app.routers.imports.crud_collection')
    @patch('app.routers.imports.get_db_connection')
    def test_import_file(self, mock_get_db_connection, mock_crud_collection, mock_task_dispatcher):
        # Arrange
        mock_db = MagicMock()
        mock_get_db_connection.return_value = mock_db
        mock_crud_collection.get_collection_by_name.return_value = MagicMock(import_type="NONE")

        file_content = b"This is a test file."
        
        # Act
        response = self.client.post(
            "/import/test_collection",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "File import started in the background."})
        mock_task_dispatcher.add_task.assert_called_once()
        mock_crud_collection.update_collection_import_type.assert_called_once()

    def test_get_imports(self):
        # Act
        response = self.client.get("/import/")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['name'], 'FILE')


if __name__ == '__main__':
    unittest.main()
