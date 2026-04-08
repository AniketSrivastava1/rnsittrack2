import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SBOMParser:
    """Parses Syft JSON output into a structured dependency dictionary."""

    def parse(self, json_str: str) -> List[Dict[str, Any]]:
        """
        Parses Syft JSON output.
        
        Args:
            json_str: The raw JSON output from syft.
            
        Returns:
            A list of dependencies with name, version, type, and path.
        """
        try:
            data = json.loads(json_str)
            artifacts = data.get("artifacts", [])
            
            dependencies = []
            for art in artifacts:
                dep = {
                    "name": art.get("name"),
                    "version": art.get("version"),
                    "type": art.get("type"),
                    "location": self._get_primary_location(art)
                }
                dependencies.append(dep)
            
            return dependencies
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Syft JSON: {e}")
            return []

    def _get_primary_location(self, artifact: Dict[str, Any]) -> str:
        """Extracts the primary file location for an artifact."""
        locations = artifact.get("locations", [])
        if locations:
            return locations[0].get("path", "unknown")
        return "unknown"

    def pretty_print(self, dependencies: List[Dict[str, Any]]) -> str:
        """Returns a human-readable representation of the dependencies."""
        if not dependencies:
            return "No dependencies found."
            
        lines = [f"{'Name':<30} | {'Version':<15} | {'Type':<10} | {'Location'}"]
        lines.append("-" * 80)
        for dep in dependencies:
            lines.append(f"{dep['name']:<30} | {dep['version']:<15} | {dep['type']:<10} | {dep['location']}")
        
        return "\n".join(lines)
