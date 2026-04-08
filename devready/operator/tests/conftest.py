import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from hypothesis import settings
    settings.register_profile("default", max_examples=10)
    settings.load_profile("default")
except ImportError:
    pass

@pytest.fixture
def mock_docker_env():
    pass
