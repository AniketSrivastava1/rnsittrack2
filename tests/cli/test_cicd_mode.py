import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from devready.cli.formatter import RichFormatter

def test_tty_detection():
    # Mock isatty to return True
    with patch("sys.stdout.isatty", return_value=True):
        formatter = RichFormatter()
        # Rich's Console might need more mocking to internally believe it's a TTY 
        # but we added our own is_interactive property
        assert formatter.console.is_terminal is True
        assert formatter.is_interactive is True

def test_non_tty_detection():
    # Mock isatty to return False
    with patch("sys.stdout.isatty", return_value=False):
        # We need to simulate that we are not in a terminal
        # Console(force_terminal=None) uses sys.stdout.isatty()
        formatter = RichFormatter()
        assert formatter.console.is_terminal is False
        assert formatter.is_interactive is False

def test_environment_override_non_interactive():
    with patch("sys.stdout.isatty", return_value=True):
        with patch.dict(os.environ, {"DEVREADY_NON_INTERACTIVE": "1"}):
            formatter = RichFormatter()
            assert formatter.is_interactive is False
