import pytest
import json
from unittest.mock import MagicMock
from devready.inspector.dependency_scanner import DependencyScanner
from devready.inspector.subprocess_wrapper import ExecutionResult
from devready.inspector.sbom_parser import SBOMParser

@pytest.fixture
def mock_wrapper():
    return MagicMock()

@pytest.fixture
def scanner(mock_wrapper):
    return DependencyScanner(wrapper=mock_wrapper)

def test_scan_success(scanner, mock_wrapper):
    # Mock Syft JSON output
    mock_data = {
        "artifacts": [
            {
                "name": "fastapi",
                "version": "0.100.0",
                "type": "python",
                "locations": [{"path": "requirements.txt"}]
            }
        ]
    }
    mock_wrapper.execute.return_value = ExecutionResult(
        command="syft . -o json",
        stdout=json.dumps(mock_data),
        stderr="",
        exit_code=0,
        duration_ms=100.0
    )
    
    result = scanner.scan(".")
    assert result["success"] is True
    assert result["count"] == 1
    assert result["dependencies"][0]["name"] == "fastapi"

def test_scan_syft_missing(scanner, mock_wrapper):
    # Simulate syft not in PATH
    mock_wrapper.execute.side_effect = FileNotFoundError("syft not found")
    
    result = scanner.scan(".")
    assert result["success"] is False
    assert "not found" in result["error"].lower()
    assert "https://github.com/anchore/syft" in result["details"]

def test_parse_empty_json():
    parser = SBOMParser()
    deps = parser.parse("{}")
    assert deps == []

def test_parse_invalid_json():
    parser = SBOMParser()
    deps = parser.parse("invalid json")
    assert deps == []
