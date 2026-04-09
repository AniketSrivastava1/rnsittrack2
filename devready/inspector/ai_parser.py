import logging
import os
from typing import Dict, Any, Optional
from devready.inspector.config_parser import ConfigParser

logger = logging.getLogger(__name__)

class AIParser:
    """Specialized parser for AI coding agent instruction files."""

    def __init__(self, config_parser: Optional[ConfigParser] = None):
        self.config_parser = config_parser or ConfigParser()

    def parse_project_configs(self, project_root: str) -> Dict[str, Any]:
        """
        Parses all AI configs in the project and merges them.
        """
        configs = self.config_parser.find_configs(project_root)
        
        merged_config = {
            "instructions": "",
            "model_preferences": {},
            "dependencies": [],
            "endpoints": [],
            "files_found": []
        }

        # Sort by precedence: general md files first, then .cursorrules (last takes precedence)
        # Precedence: .aider.conf.yml < AGENTS.md < CLAUDE.md < .cursorrules
        precedence = {
            ".aider.conf.yml": 1,
            "AGENTS.md": 2,
            "copilot-instructions.md": 3,
            "CLAUDE.md": 4,
            ".cursorrules": 5
        }
        
        sorted_configs = sorted(
            configs, 
            key=lambda x: precedence.get(x["filename"], 0)
        )

        for config in sorted_configs:
            filename = config["filename"]
            basename = os.path.basename(filename)
            content = config["content"]
            merged_config["files_found"].append(filename)
            
            if basename in ("CLAUDE.md", "copilot-instructions.md"):
                self._merge_claude_md(merged_config, content)
            elif basename == ".cursorrules":
                self._merge_cursorrules(merged_config, content)
            elif basename in (".copilot", "AGENTS.md"):
                if isinstance(content, dict) and "raw_text" in content:
                    merged_config["instructions"] += "\n" + content["raw_text"]
            # Add more as needed
            
        return merged_config

    def _merge_claude_md(self, base: Dict[str, Any], content: Dict[str, Any]):
        """Merges instructions from CLAUDE.md / copilot-instructions.md."""
        if isinstance(content, dict):
            # Try named sections first
            instr = (
                content.get("instructions", "")
                or content.get("rules", "")
                or content.get("guidelines", "")
                or content.get("copilot instructions", "")
            )
            # Fall back to combining all section text (including 'general')
            if not instr:
                instr = "\n".join(str(v) for v in content.values() if v)
            if instr:
                base["instructions"] += "\n" + str(instr)

            # Look for tech stack or dependencies
            stack = content.get("stack", "") or content.get("technology", "")
            if stack:
                base["instructions"] += "\nTech Stack Info: " + str(stack)

    def _merge_cursorrules(self, base: Dict[str, Any], content: Any):
        """Merges instructions from .cursorrules (high precedence)."""
        if isinstance(content, dict):
            # Process dictionary content (JSON/YAML)
            instr = content.get("instructions", "") or content.get("rules", "")
            if instr:
                base["instructions"] = str(instr) # High precedence: overwrite or strongly append
                
            model = content.get("model", {})
            if model:
                base["model_preferences"].update(model if isinstance(model, dict) else {"name": str(model)})
        
        elif isinstance(content, str):
            # Plain text .cursorrules
            base["instructions"] = content
