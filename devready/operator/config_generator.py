import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigGenerator(ABC):
    @abstractmethod
    def generate_isolation_config(self, project_root: str, requirements: Dict[str, Any]) -> str:
        """Generate and write isolation configuration, returning path to generated file."""
        pass
        
    def _read_existing_config(self, file_path: str) -> str:
        """Read existing configuration file if it exists."""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read config {file_path}: {e}")
        return ""

    @abstractmethod
    def validate_syntax(self, content: str) -> bool:
        """Validate the syntax of the generated config."""
        pass
