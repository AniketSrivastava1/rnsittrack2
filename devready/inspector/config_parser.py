import logging
import yaml
import json
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigParser:
    """Searches for and parses AI agent configuration files."""

    CONFIG_FILES = [
        "CLAUDE.md",
        ".cursorrules",
        ".copilot",
        "AGENTS.md",
        ".aider.conf.yml",
        ".github/copilot-instructions.md"
    ]

    def find_configs(self, project_root: str) -> List[Dict[str, Any]]:
        """
        Searches for known config files in the project root.
        """
        found_configs = []
        root_path = Path(project_root)
        
        for filename in self.CONFIG_FILES:
            file_path = root_path / filename
            if file_path.exists():
                try:
                    config_data = self.parse_file(file_path)
                    if config_data:
                        found_configs.append({
                            "file_path": str(file_path),
                            "filename": filename,
                            "content": config_data
                        })
                except Exception as e:
                    logger.error(f"Error parsing config file {file_path}: {e}")
                    
        return found_configs

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parses a configuration file based on its extension/type."""
        filename = file_path.name
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        if filename == "CLAUDE.md" or filename == "copilot-instructions.md":
            return self._parse_markdown(content)
        elif filename == ".cursorrules":
            return self._parse_json_or_yaml(content)
        elif filename.endswith(".yml") or filename.endswith(".yaml"):
            return self._parse_yaml(content)
        elif filename == ".copilot" or filename == "AGENTS.md" or filename == "rules.copilot":
            # Simple text parsing for now
            return {"raw_text": content}
        
        return {}

    def _parse_markdown(self, content: str) -> Dict[str, Any]:
        """Simple extraction of sections from a markdown file."""
        sections = {}
        current_section = "general"
        sections[current_section] = []
        
        for line in content.splitlines():
            if line.startswith("#"):
                current_section = line.lstrip("#").strip().lower()
                sections[current_section] = []
            else:
                sections[current_section].append(line)
        
        return {k: "\n".join(v).strip() for k, v in sections.items() if v}

    def _parse_json_or_yaml(self, content: str) -> Dict[str, Any]:
        """Attempts to parse as JSON first, then YAML."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._parse_yaml(content)

    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """Parses content as YAML."""
        try:
            return yaml.safe_load(content) or {}
        except Exception:
            return {"error": "Failed to parse YAML"}
