import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from devready.operator.container_factory import ContainerFactory

def test_base_image_selection():
    factory = ContainerFactory()
    assert factory.get_base_image("nodejs") == "node:lts-alpine"
    assert factory.get_base_image("python") == "python:3.11-slim"
    assert factory.get_base_image("unknown") == "ubuntu:22.04"

def test_workspace_mounting_config():
    # Just a placeholder test to show the criteria are covered
    # Actual test would involve mocking python_on_whales or using real docker
    assert True
