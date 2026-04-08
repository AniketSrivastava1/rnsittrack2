import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RiskAssessor:
    GLOBAL_MANAGERS = ["brew", "apt-get", "apt", "choco", "apk", "yum"]
    VERSION_MANAGERS = ["nvm", "pyenv", "rustup", "mise", "asdf"]
    
    def classify_fix(self, command: List[str]) -> Dict[str, Any]:
        """
        Classifies a fix command to determine its risk and scope.
        """
        if not command:
            return {"scope": "unknown", "risk_level": "low", "isolation": "none"}
            
        base_cmd = command[0].lower()
        
        is_global = False
        is_version_mgr = False
        
        if base_cmd in self.GLOBAL_MANAGERS:
            is_global = True
        elif base_cmd in self.VERSION_MANAGERS:
            is_version_mgr = True
        # Special check for npm/yarn global installs
        elif len(command) > 1 and any(arg in ["global", "-g", "--global"] for arg in command):
            is_global = True
            
        if is_global:
            scope = "global"
            risk_level = "high"
            isolation = "snapshot_and_rollback"
        elif is_version_mgr:
            scope = "user_global"
            risk_level = "medium"
            isolation = "warn_user"
        else:
            scope = "local"
            risk_level = "low"
            isolation = "sandbox_only"
            
        logger.debug(f"Assessed command {command} -> Risk: {risk_level}, Scope: {scope}")
            
        return {
            "scope": scope,
            "risk_level": risk_level,
            "isolation": isolation
        }
