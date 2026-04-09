"""Logging configuration with rotation and sensitive data redaction."""
from __future__ import annotations

import logging
import logging.handlers
import re
from pathlib import Path

_SENSITIVE_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|token|password|secret|credential)\s*[=:]\s*\S+'),
]
_REDACTED = "[REDACTED]"


class RedactingFilter(logging.Filter):
    """Redact sensitive values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._redact(str(record.msg))
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    self._redact(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {k: self._redact(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
        return True

    def _redact(self, text: str) -> str:
        for pattern in _SENSITIVE_PATTERNS:
            text = pattern.sub(_REDACTED, text)
        return text


def setup_logging(log_file: str, level: str = "INFO", max_size_mb: int = 10, backup_count: int = 5) -> None:
    """Configure root logger with rotating file handler and console handler."""
    log_path = Path(log_file).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    fmt = logging.Formatter("%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.handlers.RotatingFileHandler(
        str(log_path),
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count,
    )
    file_handler.setFormatter(fmt)
    file_handler.addFilter(RedactingFilter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.addFilter(RedactingFilter())

    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)
