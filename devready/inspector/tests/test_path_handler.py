import os
import pytest
from pathlib import Path
from devready.inspector.path_handler import PathHandler

def test_normalize_basic():
    # Test normalization on Windows (replaces \ with /)
    path = "C:\\Users\\Aniket\\Project"
    normalized = PathHandler.normalize(path)
    assert normalized == "C:/Users/Aniket/Project"

def test_normalize_expand_user():
    # Test ~ expansion
    normalized = PathHandler.normalize("~")
    assert normalized == Path(os.path.expanduser("~")).as_posix()

def test_validate_exists_success(tmp_path):
    # Test successful validation
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    path = PathHandler.validate_exists(test_file)
    assert path == test_file

def test_validate_exists_failure():
    # Test failure on non-existent path
    with pytest.raises(FileNotFoundError):
        PathHandler.validate_exists("non_existent_file_xyz_123")

def test_relative_to_root():
    root = "C:/Project"
    path = "C:/Project/src/main.py"
    rel = PathHandler.get_project_root_relative(path, root)
    assert rel == "src/main.py"
