import builtins
import os
import pytest
from pathlib import Path
from unittest import mock
import logging
from app.internal.temp_file_helper import TempFileHelper

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture to create a temporary directory for test files."""
    return tmp_path

def test_save_temp_creates_file_with_correct_content_and_extension(tmp_path):
    """
    Test that save_temp creates a file with the correct content and preserves the extension.
    """
    file_name = "test_document.docx"
    file_content = b"This is a test docx content."
    
    # Let TempFileHelper create the temporary file in the system's temp directory
    saved_path = TempFileHelper.save_temp(file_content, file_name)

    assert Path(saved_path).exists()
    assert Path(saved_path).suffix == Path(file_name).suffix
    
    with open(saved_path, 'rb') as f:
        read_content = f.read()
    assert read_content == file_content
    
    # Clean up the created file
    TempFileHelper.remove_temp(saved_path)
    assert not Path(saved_path).exists()

def test_remove_temp_deletes_file(tmp_path):
    """
    Test that remove_temp successfully deletes an existing file.
    """
    file_name = "file_to_delete.txt"
    file_path = tmp_path / file_name
    file_path.write_text("temporary content")
    
    assert file_path.exists()
    TempFileHelper.remove_temp(str(file_path))
    assert not file_path.exists()

def test_remove_temp_handles_non_existent_file(caplog):
    """
    Test that remove_temp handles attempts to delete a non-existent file gracefully.
    It should log a warning but not raise an error.
    """
    non_existent_file = "non_existent_file.pdf"
    
    with caplog.at_level(logging.WARNING):
        TempFileHelper.remove_temp(non_existent_file)
    
    assert "Attempted to remove non-existent temporary file" in caplog.text

# Test for save_temp error handling
def test_save_temp_handles_io_error(tmp_path, monkeypatch):
    """
    Test that save_temp handles IOError during file writing.
    """
    file_name = "error_file.txt"
    file_content = b"content"

    # Mock the write method of the file object returned by tempfile.NamedTemporaryFile
    # We need to mock the actual write operation that happens inside the context manager
    def mock_open_temp_file(*args, **kwargs):
        mock_file = mock.MagicMock()
        mock_file.name = str(tmp_path / "mock_temp_file.txt") # Ensure a path is returned
        mock_file.write.side_effect = IOError("Disk full")
        return mock.MagicMock(__enter__=mock.MagicMock(return_value=mock_file), __exit__=mock.MagicMock(return_value=False))

    monkeypatch.setattr(TempFileHelper.save_temp.__globals__['tempfile'], 'NamedTemporaryFile', mock_open_temp_file)
    
    with pytest.raises(IOError, match="Disk full"):
        TempFileHelper.save_temp(file_content, file_name)

# Test for remove_temp error handling (e.g., permission denied)
def test_remove_temp_handles_os_error(tmp_path, monkeypatch):
    """
    Test that remove_temp handles OSError (e.g., permission denied) during file removal.
    """
    file_name = "protected_file.txt"
    file_path = tmp_path / file_name
    file_path.write_text("protected content")

    def mock_remove(path):
        raise OSError("Permission denied")

    monkeypatch.setattr('os.remove', mock_remove)

    with pytest.raises(OSError, match="Permission denied"):
        TempFileHelper.remove_temp(str(file_path))

def test_get_temp_file_content(tmp_path):
    """
    Test that get_temp_file_content correctly retrieves content and handles errors.
    """
    # 1. Test successful content retrieval
    test_content = "Hello, this is a test."
    test_file = tmp_path / "my_test_file.txt"
    test_file.write_text(test_content, encoding='utf-8')
    
    retrieved_content = TempFileHelper.get_temp_file_content(str(test_file))
    assert retrieved_content == test_content

    # 2. Test FileNotFoundError for a non-existent file
    non_existent_file = tmp_path / "non_existent_file.txt"
    
    with pytest.raises(FileNotFoundError):
        TempFileHelper.get_temp_file_content(str(non_existent_file))
