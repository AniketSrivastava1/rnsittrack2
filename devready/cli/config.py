import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    DEFAULT_CONFIG = {
        "daemon_url": "http://localhost:8443",
        "output_format": "text",
        "color": "auto",
        "default_scan_scope": "full",
    }
    
    def __init__(self):
        self.config_path = Path.home() / ".devready" / "cli-config.yaml"
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        if not self.config_path.exists():
            return self.DEFAULT_CONFIG.copy()
        try:
            with open(self.config_path) as f:
                user_config = yaml.safe_load(f)
            config = self.DEFAULT_CONFIG.copy()
            if user_config:
                config.update(user_config)
            return config
        except Exception:
            return self.DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save_config()
    
    def save_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f)
