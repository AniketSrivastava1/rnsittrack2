import subprocess
import time
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    """Stores the result of a subprocess execution."""
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    timed_out: bool = False

class SubprocessError(Exception):
    """Raised when a subprocess execution fails."""
    def __init__(self, result: ExecutionResult):
        self.result = result
        super().__init__(f"Command '{result.command}' failed with exit code {result.exit_code}: {result.stderr}")

class SubprocessWrapper:
    """Wrapper for executing system commands safely and consistently."""

    def execute(self, args: List[str], timeout_seconds: float = 5.0) -> ExecutionResult:
        """
        Executes a command and returns the result.
        
        Args:
            args: List of command arguments (e.g., ["ls", "-l"]).
            timeout_seconds: Maximum time to wait for the command to finish.
            
        Returns:
            ExecutionResult containing stdout, stderr, exit code, and duration.
            
        Raises:
            SubprocessError: if the process exits with a non-zero code.
        """
        command_str = " ".join(args)
        # Sanitize: ensure args is a list to prevent shell injection
        if not isinstance(args, list):
            raise ValueError("Arguments must be provided as a list for security.")

        logger.debug(f"Executing command: {command_str}")
        start_time = time.perf_counter()
        
        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False  # Crucial for security
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                result = ExecutionResult(
                    command=command_str,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=process.returncode,
                    duration_ms=duration_ms
                )
                
                if process.returncode != 0:
                    logger.warning(f"Command failed: {command_str} (Exit code: {process.returncode})")
                    raise SubprocessError(result)
                
                return result

            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(f"Command timed out after {timeout_seconds}s: {command_str}")
                
                return ExecutionResult(
                    command=command_str,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=-1,
                    duration_ms=duration_ms,
                    timed_out=True
                )

        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug("Command not available: %s", command_str)
            raise
