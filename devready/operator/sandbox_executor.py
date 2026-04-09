import logging
import time
import threading
from typing import Dict, Any, List
from python_on_whales import Container
from python_on_whales.exceptions import DockerException
from devready.operator.resource_cleaner import ResourceCleaner

logger = logging.getLogger(__name__)

class SandboxExecutor:
    def __init__(self):
        self.cleaner = ResourceCleaner()

    def execute_in_sandbox(self, container: Container, command: List[str], timeout: int = 60) -> Dict[str, Any]:
        """
        Execute a fix command inside the provided container.
        """
        start_time = time.time()
        logger.debug(f"Executing command in sandbox: {command} with timeout {timeout}s")
        
        result = {
            "command": command,
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "verified": False,
            "duration": 0.0,
            "timed_out": False
        }
        
        def run_cmd():
            try:
                out = container.execute(command)
                result["stdout"] = out
                result["exit_code"] = 0
            except DockerException as e:
                result["stderr"] = str(e)
                result["exit_code"] = getattr(e, 'return_code', 1)
            except Exception as e:
                result["stderr"] = str(e)
                result["exit_code"] = 1
        
        thread = threading.Thread(target=run_cmd)
        thread.start()
        thread.join(timeout)
        
        duration = time.time() - start_time
        result["duration"] = duration
        
        if thread.is_alive():
            logger.warning(f"Command {command} timed out after {timeout} seconds, terminating container.")
            result["timed_out"] = True
            result["exit_code"] = 124
            try:
                container.kill()
            except Exception as e:
                logger.error(f"Failed to kill container after timeout: {e}")
        else:
            if result["exit_code"] == 0:
                result["verified"] = True

        # Always clean up the container
        try:
            self.cleaner.cleanup_sandbox(container.id)
        except Exception:
            pass
                
        logger.debug(f"Execution finished. Verified: {result['verified']}, Exit code: {result['exit_code']}, Duration: {duration:.2f}s")
        return result
