import os
import logging
import re
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EnvCollector:
    """Collects and redacts environment variables."""

    # Patterns that indicate a value is sensitive
    SENSITIVE_PATTERNS = [
        r"token", r"key", r"secret", r"password", r"api", r"auth", r"pwd", r"credential"
    ]

    # Keys that are relevant for development and safe to log (mostly)
    DEV_RELEVANT_KEYS = {
        "PATH", "NODE_ENV", "PYTHONPATH", "GOPATH", "CARGO_HOME", "JAVA_HOME",
        "OS", "PROCESSOR_ARCHITECTURE", "USER", "USERNAME", "HOME", "USERPROFILE"
    }

    def collect(self, project_root: Optional[str] = None) -> Dict[str, str]:
        """
        Collects redacted environment variables from the current process and .env files.
        """
        env_vars = {}
        
        # 1. Collect from current process
        for key, value in os.environ.items():
            env_vars[key] = self.redact_if_sensitive(key, value)
            
        # 2. Collect from .env file in project root if it exists
        if project_root:
            env_path = Path(project_root) / ".env"
            if env_path.exists():
                env_vars.update(self.parse_env_file(env_path))
                
        return env_vars

    def redact_if_sensitive(self, key: str, value: str) -> str:
        """Checks if a key is sensitive and redacts its value if so."""
        key_lower = key.lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, key_lower):
                return "[REDACTED]"
        return value

    def parse_env_file(self, file_path: Path) -> Dict[str, str]:
        """Parses a .env file and returns redacted key-value pairs."""
        collected = {}
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'").strip('"')
                    collected[key] = self.redact_if_sensitive(key, value)
                else:
                    logger.warning(f"Skipping malformed line in .env: {line}")
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
            
        return collected

    def get_filtered_env(self, env_vars: Dict[str, str]) -> Dict[str, str]:
        """Returns only the development-relevant and redacted environment variables."""
        filtered = {}
        for key in self.DEV_RELEVANT_KEYS:
            if key in env_vars:
                filtered[key] = env_vars[key]
        return filtered
