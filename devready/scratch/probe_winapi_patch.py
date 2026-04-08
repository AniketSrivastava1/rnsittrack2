import _winapi
import sys

# Store original for testing
orig = _winapi.CreateProcess

def test_patch(*args):
    print("Monkeypatch active!")
    # We won't actually call the original here to avoid spawning anything in the probe
    return None

try:
    _winapi.CreateProcess = test_patch
    print("SUCCESS: _winapi.CreateProcess is monkeypatchable")
except Exception as e:
    print(f"FAILURE: _winapi.CreateProcess is not monkeypatchable: {e}")
