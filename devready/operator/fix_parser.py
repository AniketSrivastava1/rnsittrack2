import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FixParser:
    PACKAGE_MANAGERS = ["npm", "yarn", "pnpm", "bun", "pip", "poetry", "pipenv", "cargo", "go", "brew", "apt", "choco", "nvm", "pyenv"]
    
    def parse_command(self, cmd_string: str) -> Dict[str, Any]:
        parts = cmd_string.split()
        if not parts:
            return {}
            
        manager = parts[0]
        if manager not in self.PACKAGE_MANAGERS:
            manager = "unknown"
            
        action = parts[1] if len(parts) > 1 else "unknown"
        target = parts[2] if len(parts) > 2 else "unknown"
        
        version = None
        if "@" in target:
            target, version = target.split("@", 1)
        elif "==" in target:
            target, version = target.split("==", 1)
            
        return {
            "package_manager": manager,
            "action": action,
            "target": target,
            "version": version,
            "original": cmd_string
        }

class PrettyPrinter:
    def format_fix(self, parsed_fix: Dict[str, Any], risk_level: str, isolation: str) -> str:
        cmd = parsed_fix.get("original", "")
        pkg = parsed_fix.get("target", "unknown")
        action = parsed_fix.get("action", "unknown")
        
        return f"[FIX] {action.capitalize()} {pkg}\n Command: {cmd}\n Risk: {risk_level.upper()}\n Isolation: {isolation}"
