import pytest
import sys
from devready.inspector.subprocess_wrapper import SubprocessWrapper, SubprocessError

@pytest.fixture
def wrapper():
    return SubprocessWrapper()

def test_execute_success(wrapper):
    # 'echo' works on both Windows and Unix
    # Use a command that is definitely available
    args = ["cmd", "/c", "echo", "hello"] if sys.platform == "win32" else ["echo", "hello"]
    result = wrapper.execute(args)
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.duration_ms > 0
    assert not result.timed_out

def test_execute_failure(wrapper):
    # 'exit 1' equivalent
    args = ["cmd", "/c", "exit", "1"] if sys.platform == "win32" else ["sh", "-c", "exit 1"]
    with pytest.raises(SubprocessError) as excinfo:
        wrapper.execute(args)
    assert excinfo.value.result.exit_code != 0

def test_execute_timeout(wrapper):
    # Use python to sleep as it's cross-platform and doesn't fail on redirected input
    args = [sys.executable, "-c", "import time; time.sleep(2)"]
    
    result = wrapper.execute(args, timeout_seconds=0.5)
    assert result.timed_out is True
    assert result.exit_code == -1

def test_shell_injection_prevention(wrapper):
    # The goal is to show that passing a list with shell=False
    # prevents the arguments from being interpreted as shell commands.
    if sys.platform == "win32":
        # If we use cmd /c, cmd will parse its arguments. 
        # To test injection prevention, we should use a command that doesn't parse sub-commands.
        # But most things on Windows are run through cmd.
        # Let's use a simple python command to verify arguments are passed as-is.
        args = [sys.executable, "-c", "import sys; print(sys.argv[1:])", "hello & whoami"]
        result = wrapper.execute(args)
        assert "hello & whoami" in result.stdout
        assert "aniketsrivastava" not in result.stdout.lower()
    else:
        args = ["echo", "hello; whoami"]
        result = wrapper.execute(args)
        assert "hello; whoami" in result.stdout
