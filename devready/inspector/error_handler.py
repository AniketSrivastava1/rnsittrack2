import logging
import time
from typing import List, Dict

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Handles errors during the scanning process."""

    def __init__(self):
        self.errors: List[Dict[str, str]] = []

    def handle(self, component: str, error: Exception):
        """Logs and records an error from a component."""
        error_msg = str(error)
        logger.error(f"Error in component '{component}': {error_msg}")
        
        self.errors.append({
            "component": component,
            "message": error_msg,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })

    def get_errors(self) -> List[Dict[str, str]]:
        """Returns the list of recorded errors."""
        return self.errors

    def has_errors(self) -> bool:
        """Returns True if any errors were recorded."""
        return len(self.errors) > 0
