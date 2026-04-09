import os
import logging
import toml
from typing import Dict, Any
from devready.operator.config_generator import ConfigGenerator

logger = logging.getLogger(__name__)

class MiseGenerator(ConfigGenerator):
    def validate_syntax(self, content: str) -> bool:
        try:
            toml.loads(content)
            return True
        except Exception as e:
            logger.error(f"Invalid TOML syntax in mise config: {e}")
            return False

    def generate_isolation_config(self, project_root: str, requirements: Dict[str, Any]) -> str:
        target_path = os.path.join(project_root, "mise.toml")
        
        settings = self._read_existing_config(target_path)
        config_data = {}
        if settings:
            try:
                config_data = toml.loads(settings)
            except Exception:
                logger.warning("Could not parse existing mise.toml, rewriting from scratch.")
        
        if "tools" not in config_data:
            config_data["tools"] = {}
            
        tools_req = requirements.get("tools", {})
        for tool, version in tools_req.items():
            config_data["tools"][tool] = version
            
        new_content = toml.dumps(config_data)
        instruction_header = "# DevReady auto-generated mise.toml\n"
        instruction_header += "# Isolation Strategy: Defines precise tool versions.\n"
        instruction_header += "# Install mise: curl https://mise.run | sh\n"
        instruction_header += "# Run 'mise install' to ensure tools are ready\n\n"
        
        final_content = instruction_header + new_content
        
        if not self.validate_syntax(new_content):
            raise ValueError("Generated mise.toml has syntax errors")
            
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            logger.info(f"Generated mise config at {target_path}")
            return target_path
        except Exception as e:
            logger.error(f"Failed to write mise.toml: {e}")
            raise
