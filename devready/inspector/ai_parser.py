"""AI agent config parser — discovers, parses and merges all AI coding agent config files."""
import logging
import os
from typing import Dict, Any, List, Optional

from devready.inspector.config_parser import ConfigParser

logger = logging.getLogger(__name__)

# Files treated as carrying the "central" team rules (golden source of truth)
_CENTRAL_FILES = {"CLAUDE.md", "AGENTS.md"}

# Files treated as agent-specific local configs (compared against central)
_AGENT_FILES = {
    "copilot-instructions.md",
    ".cursorrules",
    ".windsurfrules",
    ".copilot",
    ".codex",
    "codex.md",
    ".aider.conf.yml",
}

# Merge precedence: higher number = merged later = its instructions win on conflict
_PRECEDENCE = {
    ".aider.conf.yml": 1,
    "AGENTS.md": 2,
    "codex.md": 3,
    ".codex": 4,
    "copilot-instructions.md": 5,
    "CLAUDE.md": 6,
    ".cursorrules": 7,
    ".windsurfrules": 8,
}


class AIParser:
    """Specialized parser for AI coding agent instruction files.
    
    Responsibilities:
    1. Discover all AI config files in a project (CLAUDE.md, .cursorrules, Copilot, Codex, etc.)
    2. Merge their instructions into a single unified config
    3. Compare agent-specific configs against the central golden files (CLAUDE.md / AGENTS.md)
       and report rules that are missing from agent configs
    """

    def __init__(self, config_parser: Optional[ConfigParser] = None):
        self.config_parser = config_parser or ConfigParser()

    def parse_project_configs(self, project_root: str) -> Dict[str, Any]:
        """Parse all AI configs in the project and return a merged view."""
        configs = self.config_parser.find_configs(project_root)

        merged_config: Dict[str, Any] = {
            "instructions": "",
            "model_preferences": {},
            "dependencies": [],
            "endpoints": [],
            "files_found": [],
            # Central vs agent-specific breakdown for drift detection
            "central_instructions": "",
            "agent_instructions": {},  # basename -> instructions text
        }

        sorted_configs = sorted(
            configs,
            key=lambda x: _PRECEDENCE.get(os.path.basename(x["filename"]), 0)
        )

        for config in sorted_configs:
            filename = config["filename"]
            basename = os.path.basename(filename)
            content = config["content"]
            merged_config["files_found"].append(filename)

            instr = self._extract_instructions(basename, content)
            if not instr:
                continue

            # Accumulate in merged view
            merged_config["instructions"] += "\n" + instr

            # Track separately: central vs agent configs
            if basename in _CENTRAL_FILES:
                merged_config["central_instructions"] += "\n" + instr
            else:
                merged_config["agent_instructions"][basename] = instr

            # Model preferences (from .cursorrules / .windsurfrules JSON)
            if isinstance(content, dict):
                model = content.get("model", {})
                if model:
                    merged_config["model_preferences"].update(
                        model if isinstance(model, dict) else {"name": str(model)}
                    )

        return merged_config

    def get_central_drift(self, project_root: str) -> List[Dict[str, Any]]:
        """Compare agent-specific configs against central CLAUDE.md / AGENTS.md.
        
        Returns a list of drift items: rules defined in the central file but
        missing from one or more agent configs.
        """
        parsed = self.parse_project_configs(project_root)
        central = parsed["central_instructions"].strip().lower()
        agent_configs = parsed["agent_instructions"]

        if not central or not agent_configs:
            return []

        drift_items = []
        # Extract non-empty lines from central as candidate rules
        central_rules = [
            line.strip()
            for line in central.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

        for agent_file, agent_text in agent_configs.items():
            agent_lower = agent_text.lower()
            missing = [r for r in central_rules if r not in agent_lower]
            if missing:
                drift_items.append({
                    "agent_file": agent_file,
                    "missing_rules": missing,
                    "message": (
                        f"{agent_file} is missing {len(missing)} rule(s) "
                        f"defined in the central AI config"
                    ),
                })
        return drift_items

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_instructions(self, basename: str, content: Any) -> str:
        """Extract instructions text from parsed config content."""
        if basename in ("CLAUDE.md", "copilot-instructions.md", "codex.md", "AGENTS.md"):
            return self._text_from_markdown_dict(content)
        elif basename in (".cursorrules", ".windsurfrules"):
            return self._text_from_cursorrules(content)
        elif basename in (".copilot", ".codex"):
            if isinstance(content, dict):
                return content.get("raw_text", "")
            return str(content) if content else ""
        elif basename.endswith((".yml", ".yaml")):
            if isinstance(content, dict):
                return content.get("instructions", "") or content.get("rules", "")
        return ""

    def _text_from_markdown_dict(self, content: Any) -> str:
        """Pull text from a parsed markdown section dict (or plain string)."""
        if isinstance(content, str):
            return content
        if not isinstance(content, dict):
            return ""
        # Try canonical section names first
        instr = (
            content.get("instructions", "")
            or content.get("rules", "")
            or content.get("guidelines", "")
            or content.get("copilot instructions", "")
        )
        if instr:
            return str(instr)
        # Fall back: concatenate all section values
        return "\n".join(str(v) for v in content.values() if v)

    def _text_from_cursorrules(self, content: Any) -> str:
        """Pull text from .cursorrules (JSON/YAML dict or plain string)."""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            return str(
                content.get("instructions", "")
                or content.get("rules", "")
                or ""
            )
        return ""
