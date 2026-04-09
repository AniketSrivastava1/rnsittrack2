import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from devready.operator.errors import DockerNotAvailableError, FixExecutionError, ErrorHandler

def test_docker_error():
    err = DockerNotAvailableError()
    assert "Docker daemon is not running" in str(err)

def test_error_handler():
    results = [
        {"success": False, "error": "Network timeout"},
        {"success": False, "error": "Permission denied"}
    ]
    summary = ErrorHandler.handle_execution_results(results)
    assert summary["all_failed"] is True
    assert len(summary["errors"]) == 2
