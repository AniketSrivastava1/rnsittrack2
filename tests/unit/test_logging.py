"""Unit tests for logging configuration."""
import logging
import tempfile
from pathlib import Path

from devready.daemon.logging_config import RedactingFilter, setup_logging


def test_log_file_created():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = str(Path(tmpdir) / "daemon.log")
        setup_logging(log_file)
        logging.getLogger("test").info("hello")
        assert Path(log_file).exists()


def test_sensitive_data_redacted():
    f = RedactingFilter()
    record = logging.LogRecord("test", logging.INFO, "", 0, "api_key=supersecret123", (), None)
    f.filter(record)
    assert "supersecret123" not in record.msg
    assert "[REDACTED]" in record.msg


def test_token_redacted():
    f = RedactingFilter()
    record = logging.LogRecord("test", logging.INFO, "", 0, "token=abc123xyz", (), None)
    f.filter(record)
    assert "abc123xyz" not in record.msg
