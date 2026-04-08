import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class StackDetector:
    """Detects the technology stacks used in a project."""

    STACK_MARKERS = {
        "Node.js": ["package.json", "node_modules", "yarn.lock", "package-lock.json"],
        "Python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "poetry.lock"],
        "Go": ["go.mod", "go.sum", "vendor"],
        "Rust": ["Cargo.toml", "Cargo.lock"],
        "Java": ["pom.xml", "build.gradle", "build.gradle.kts", "gradlew"],
    }

    def detect(self, project_root: str) -> List[str]:
        """
        Detects all tech stacks found in the project root.
        """
        detected_stacks = []
        root_path = Path(project_root)
        
        if not root_path.exists():
            return ["unknown"]

        for stack, markers in self.STACK_MARKERS.items():
            for marker in markers:
                if (root_path / marker).exists():
                    detected_stacks.append(stack)
                    break
        
        return detected_stacks if detected_stacks else ["unknown"]
