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
            relationships = data.get("relationships", [])
            
            # Map of artifact ID to our internal node format
            id_to_node = {}
            nodes = []
            for art in artifacts:
                node = {
                    "id": art.get("id"),
                    "name": art.get("name"),
                    "version": art.get("version"),
                    "type": art.get("type"),
                    "location": self._get_primary_location(art)
                }
                id_to_node[node["id"]] = node
                nodes.append(node)
            
            # Extract links
            links = []
            for rel in relationships:
                # Syft uses source/target IDs
                source = rel.get("source")
                target = rel.get("target")
                rel_type = rel.get("type")
                
                # We only care about dependency-like relationships
                if source in id_to_node and target in id_to_node:
                    links.append({"source": source, "target": target, "type": rel_type})
            
            return {
                "dependencies": nodes,
                "graph": {
                    "nodes": nodes,
                    "links": links
                }
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Syft JSON: {e}")
            return {"dependencies": [], "graph": {"nodes": [], "links": []}}

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
