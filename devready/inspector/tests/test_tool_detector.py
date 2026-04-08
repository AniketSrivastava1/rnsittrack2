import pytest
from unittest.mock import MagicMock
from devready.inspector.tool_detector import ToolDetector
from devready.inspector.subprocess_wrapper import ExecutionResult

@pytest.fixture
def mock_wrapper():
    return MagicMock()

@pytest.fixture
def detector(mock_wrapper):
    return ToolDetector(wrapper=mock_wrapper)

def test_parse_version_node():
    detector = ToolDetector()
    assert detector.parse_version("v18.16.0") == "18.16.0"

def test_parse_version_python():
    detector = ToolDetector()
    assert detector.parse_version("Python 3.10.12") == "3.10.12"

def test_parse_version_git():
    detector = ToolDetector()
    assert detector.parse_version("git version 2.34.1") == "2.34.1"

def test_get_version_success(detector, mock_wrapper):
    mock_wrapper.execute.return_value = ExecutionResult(
        command="node --version",
        stdout="v20.5.0\n",
        stderr="",
        exit_code=0,
        duration_ms=10.0
    )
    version = detector.get_version(["node", "--version"])
    assert version == "20.5.0"

def test_get_version_not_found(detector, mock_wrapper):
    mock_wrapper.execute.side_effect = Exception("not found")
    version = detector.get_version(["nonexistent", "--version"])
    assert version is None

def test_detect_all(detector, mock_wrapper):
    # Mock multiple calls to execute
    mock_wrapper.execute.return_value = ExecutionResult(
        command="cmd", stdout="1.2.3", stderr="", exit_code=0, duration_ms=1.0
    )
    results = detector.detect_all()
    assert "tools" in results
    assert "node" in results["tools"]
    assert results["tools"]["node"] == "1.2.3"
