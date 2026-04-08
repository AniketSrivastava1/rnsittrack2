import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from docker_manager import DockerManager
from hypothesis import given, strategies as st

def test_docker_availability_detection():
    # Property 1: Docker Availability Check
    manager = DockerManager()
    
    class MockClient:
        def info(self): return True
        def version(self):
            class MockServer: version = "24.0.0"
            class MockVersion: server = MockServer()
            return MockVersion()
            
    manager.client = MockClient()
    assert manager.verify_docker_available() is True
    assert manager.get_docker_version() == "24.0.0"
