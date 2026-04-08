import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages CLI configuration stored in ~/.devready/cli-config.yaml"""
    
    DEFAULT_CONFIG = {
        "daemon_url": "http://localhost:8443",
        "output_format": "text",  # text, json
        "color": "auto",  # auto, always, never
        "default_scan_scope": "full",
        "log_level": "INFO",
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".devready" / "cli-config.yaml"
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, creating defaults if missing."""
        if not self.config_path.exists():
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, "r") as f:
                user_config = yaml.safe_load(f)
            
            # Merge with defaults
            config = self.DEFAULT_CONFIG.copy()
            if isinstance(user_config, dict):
                config.update(user_config)
            return config
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_path}: {e}. Using defaults.")
            return self.DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value and save to file."""
        self.config[key] = value
        self.save_config()
    
    def save_config(self):
        """Save current configuration to the config file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
