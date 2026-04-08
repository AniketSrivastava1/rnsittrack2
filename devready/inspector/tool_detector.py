import re
import logging
from typing import List, Dict, Any, Optional
from devready.inspector.subprocess_wrapper import SubprocessWrapper

logger = logging.getLogger(__name__)

class ToolDetector:
    """Detects installed tools and their versions."""

    def __init__(self, wrapper: Optional[SubprocessWrapper] = None):
        self.wrapper = wrapper or SubprocessWrapper()
        self.tools_to_check = {
            "node": ["node", "--version"],
            "python": ["python", "--version"], # or py
            "go": ["go", "version"],
            "rustc": ["rustc", "--version"],
            "java": ["java", "-version"],
            "docker": ["docker", "--version"],
            "git": ["git", "--version"],
        }
        self.version_managers = {
            "nvm": ["nvm", "--version"],
            "pyenv": ["pyenv", "--version"],
            "asdf": ["asdf", "--version"],
            "mise": ["mise", "--version"],
            "rustup": ["rustup", "--version"],
            "sdkman": ["sdk", "version"],
        }

    def detect_all(self) -> Dict[str, Any]:
        """Detects all tools and version managers."""
        results = {
            "tools": {},
            "version_managers": {}
        }

        # Check main tools
        for tool, cmd in self.tools_to_check.items():
            results["tools"][tool] = self.get_version(cmd)

        # Check version managers
        for vm, cmd in self.version_managers.items():
            results["version_managers"][vm] = self.get_version(cmd)

        return results

    def get_version(self, command: List[str]) -> Optional[str]:
        """Runs a version command and parses the output."""
        try:
            # We use 1s timeout per tool as per requirement
            result = self.wrapper.execute(command, timeout_seconds=1.0)
            if result.exit_code == 0 or (command[0] == "java" and result.exit_code != 0):
                # Java often prints version to stderr
                output = result.stdout + result.stderr
                return self.parse_version(output)
            return None
        except Exception:
            return None

    def parse_version(self, output: str) -> Optional[str]:
        """Extracts a semantic version string from command output."""
        # Look for something like 1.2.3 or v1.2.3
        match = re.search(r"v?(\d+\.\d+\.\d+(?:-[a-zA-Z0-9.]+)?(?:\\+[a-zA-Z0-9.]+)? )", output)
        if match:
            return match.group(0).strip().lstrip('v')
        
        # Fallback for simpler versions like "3.10" or "17"
        match = re.search(r"(\d+\.\d+(\.\d+)?)", output)
        if match:
            return match.group(0).strip()
            
        return None
