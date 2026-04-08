import os
import json
import logging
from typing import Dict, Any
from devready.operator.config_generator import ConfigGenerator

logger = logging.getLogger(__name__)

class DevcontainerGenerator(ConfigGenerator):
    def validate_syntax(self, content: str) -> bool:
        try:
            json.loads(content)
            return True
        except Exception as e:
            logger.error(f"Invalid JSON syntax in devcontainer config: {e}")
            return False

    def generate_isolation_config(self, project_root: str, requirements: Dict[str, Any]) -> str:
        devcontainer_dir = os.path.join(project_root, ".devcontainer")
        if not os.path.exists(devcontainer_dir):
            os.makedirs(devcontainer_dir, exist_ok=True)
            
        target_path = os.path.join(devcontainer_dir, "devcontainer.json")
        
        existing_content = self._read_existing_config(target_path)
        config_data = {}
        if existing_content:
            try:
                config_data = json.loads(existing_content)
            except Exception:
                logger.warning("Could not parse existing devcontainer.json, rebuilding.")

        tech_stack = requirements.get("tech_stack", "ubuntu")
        
        if tech_stack == "nodejs":
            image = "mcr.microsoft.com/devcontainers/javascript-node:18"
        elif tech_stack == "python":
            image = "mcr.microsoft.com/devcontainers/python:3.11"
        else:
            image = "mcr.microsoft.com/devcontainers/base:ubuntu"
            
        config_data["image"] = config_data.get("image", image)
        
        ports = config_data.get("forwardPorts", [])
        for p in [3000, 8000, 8080, 5173]:
            if p not in ports:
                ports.append(p)
        config_data["forwardPorts"] = ports
        
        features = config_data.get("features", {})
        tools = requirements.get("tools", {})
        if "node" in tools:
            features["ghcr.io/devcontainers/features/node:1"] = {"version": tools["node"]}
        config_data["features"] = features
        
        if "postCreateCommand" not in config_data:
            config_data["postCreateCommand"] = requirements.get("install_cmd", "echo 'Ready'")
            
        config_data["_comment"] = "DevReady isolation strategy: Defines reproducible dev environment."
        
        new_content = json.dumps(config_data, indent=4)
        
        if not self.validate_syntax(new_content):
            raise ValueError("Generated devcontainer.json is invalid")
            
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"Generated devcontainer config at {target_path}")
            return target_path
        except Exception as e:
            logger.error(f"Failed to write devcontainer.json: {e}")
            raise
