import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class RootDetector:
    """Detects the project root directory using common markers."""

    MARKERS = {
        ".git",
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "requirements.txt"
    }

    def detect(self, start_path: Optional[str] = None, max_depth: int = 10) -> Optional[str]:
        """
        Traverses up from start_path to find the project root.
        """
        current = Path(start_path or os.getcwd()).resolve()
        
        for _ in range(max_depth):
            # Check for high priority .git marker
            if (current / ".git").exists():
                return str(current).replace("\\", "/")
            
            # Check for other markers
            for marker in self.MARKERS:
                if (current / marker).exists():
                    return str(current).replace("\\", "/")
            
            # Move up
            parent = current.parent
            if parent == current: # Reached root of filesystem
                break
            current = parent
            
        return None

    def get_project_name(self, root_path: str) -> str:
        """Extracts the project name from the root directory or manifest."""
        root = Path(root_path)
        
        # 1. Try pyproject.toml (Python)
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except Exception:
                pass
                
        # 2. Try package.json (Node.js)
        package_json = root / "package.json"
        if package_json.exists():
            try:
                import json
                data = json.loads(package_json.read_text(encoding="utf-8"))
                return data.get("name", root.name)
            except Exception:
                pass
                
        # Fallback to directory name
        return root.name
