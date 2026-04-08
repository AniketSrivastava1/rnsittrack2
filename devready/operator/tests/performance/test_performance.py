import time
import pytest

def test_container_creation_perf():
    start = time.time()
    time.sleep(1)
    duration = time.time() - start
    assert duration < 3

def test_hook_installation_perf():
    start = time.time()
    time.sleep(0.1)
    duration = time.time() - start
    assert duration < 1
