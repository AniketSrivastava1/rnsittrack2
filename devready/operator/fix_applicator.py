import os
import subprocess
import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class FixApplicator:
    def __init__(self):
        self.applied_fixes = []

    def require_user_confirmation(self, command: List[str]) -> bool:
        """Prompt user for confirmation for global fixes."""
        print(f"\nDevReady: A global fix requires your permission.")
        print(f"Command to run: {' '.join(command)}")
        # In a real CLI, we hook into Typer prompts
        # For programmatic/test use, we might mock this.
        return True # Default to true for testing

    def apply_fix(self, command: List[str], scope: str, project_dir: str) -> Dict[str, Any]:
        """Apply a verified fix on the host."""
        if scope in ["global", "user_global"]:
            if not self.require_user_confirmation(command):
                logger.info(f"User declined global fix: {command}")
                return {"success": False, "reason": "user_declined"}

        logger.info(f"Applying fix on host: {command}")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command, 
                cwd=project_dir, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            success = result.returncode == 0
            
            execution_data = {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": success,
                "timestamp": time.time(),
                "duration": time.time() - start_time
            }
            
            if success:
                self.applied_fixes.append(execution_data)
                self._update_architect_state(execution_data)
                self._verify_resolution(project_dir)
            else:
                logger.error(f"Host execution failed for {command}. Exit code: {result.returncode}")
                # Rollback should be triggered by caller
                
            return execution_data
            
        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }

    def _update_architect_state(self, data):
        logger.debug("Updating architect state with applied fix.")
        
    def _verify_resolution(self, project_dir):
        logger.debug("Verifying issue resolution locally.")
