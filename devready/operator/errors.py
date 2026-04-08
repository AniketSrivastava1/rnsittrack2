import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class OperatorError(Exception):
    """Base exception for DevReady Operator."""
    pass

class DockerNotAvailableError(OperatorError):
    """Raised when Docker is not available or reachable."""
    def __init__(self, message="Docker daemon is not running or not reachable. Please install Docker Desktop and start it."):
        super().__init__(message)

class FixExecutionError(OperatorError):
    """Raised when a fix execution fails."""
    def __init__(self, command: str, details: str):
        self.command = command
        self.details = details
        super().__init__(f"Fix execution failed for command '{command}': {details}")

class ConfigurationError(OperatorError):
    """Raised on config syntax errors."""
    pass

class ErrorHandler:
    @staticmethod
    def handle_execution_results(results: List[Dict[str, Any]]):
        """Process results, log errors, provide guidance without crashing."""
        all_failed = True
        errors = []
        
        for res in results:
            if res.get("success", False) or res.get("sandbox_success", False):
                all_failed = False
            if "error" in res:
                errors.append(res)
                logger.error(f"Error executing fix: {res.get('error')}")
                
        if all_failed and results:
            print("\nDevReady Troubleshooting:")
            print("All fixes failed. Please check your network connection, or run devready scan --verbose.")
            
        return {"errors": errors, "all_failed": all_failed}
