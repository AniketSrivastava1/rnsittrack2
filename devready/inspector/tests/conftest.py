import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock

@pytest.fixture
def mock_project_root(tmp_path):
    """Creates a mock project structure."""
    project = tmp_path / "mock_project"
    project.mkdir()
    (project / ".git").mkdir()
    (project / "pyproject.toml").write_text("[project]\nname='mock-project'")
    return project

@pytest.fixture
def mock_subprocess_wrapper():
    """Returns a mocked SubprocessWrapper."""
    from devready.inspector.subprocess_wrapper import SubprocessWrapper
    wrapper = MagicMock(spec=SubprocessWrapper)
    return wrapper
