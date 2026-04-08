import logging
from typing import Dict, Any, Optional
from devready.inspector.subprocess_wrapper import SubprocessWrapper, SubprocessError
from devready.inspector.sbom_parser import SBOMParser

logger = logging.getLogger(__name__)

class DependencyScanner:
    """Scans projects for dependencies using Syft."""

    def __init__(self, wrapper: Optional[SubprocessWrapper] = None, parser: Optional[SBOMParser] = None):
        self.wrapper = wrapper or SubprocessWrapper()
        self.parser = parser or SBOMParser()

    def scan(self, project_path: str) -> Dict[str, Any]:
        """
        Runs a Syft scan on the given project path.
        
        Returns:
            A dictionary containing the dependencies or error info.
        """
        # Command: syft <path> -o json
        # We assume 'syft' might not be in the path, so we'll handle failure
        command = ["syft", project_path, "-o", "json"]
        
        try:
            # Requirements say 4 seconds timeout for SBOM generation
            result = self.wrapper.execute(command, timeout_seconds=4.0)
            
            if result.exit_code == 0:
                dependencies = self.parser.parse(result.stdout)
                return {
                    "success": True,
                    "dependencies": dependencies,
                    "count": len(dependencies),
                    "duration_ms": result.duration_ms
                }
            else:
                return {
                    "success": False,
                    "error": f"Syft execution failed: {result.stderr}",
                    "details": "Ensure Syft is installed and accessible in your PATH. Visit https://github.com/anchore/syft for installation instructions."
                }
                
        except SubprocessError as e:
            # This happens if exit code != 0, which we already handle for 'syft' specifically
            return {
                "success": False,
                "error": str(e),
                "details": "Syft failed to execute."
            }
        except Exception as e:
            if "not found" in str(e).lower() or "FileNotFoundError" in str(type(e)):
                 return {
                    "success": False,
                    "error": "Syft command not found.",
                    "details": "Syft is required for dependency scanning. Install it from: https://github.com/anchore/syft"
                }
            return {
                "success": False,
                "error": str(e),
                "details": "An unexpected error occurred during dependency scanning."
            }
