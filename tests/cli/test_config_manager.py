import pytest
import yaml
from pathlib import Path
from devready.cli.config_manager import ConfigManager

def test_load_default_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    manager = ConfigManager(config_path=config_file)
    assert manager.get("daemon_url") == "http://localhost:8443"
    assert manager.get("color") == "auto"

def test_load_existing_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    user_config = {"daemon_url": "http://other:8443", "color": "always"}
    with open(config_file, "w") as f:
        yaml.dump(user_config, f)
    
    manager = ConfigManager(config_path=config_file)
    assert manager.get("daemon_url") == "http://other:8443"
    assert manager.get("color") == "always"
    # Merged with defaults
    assert manager.get("output_format") == "text"

def test_set_and_save_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    manager = ConfigManager(config_path=config_file)
    manager.set("color", "never")
    
    # Check if file was updated
    with open(config_file, "r") as f:
        saved_config = yaml.safe_load(f)
    assert saved_config["color"] == "never"

def test_invalid_yaml_fallback(tmp_path):
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        f.write("invalid: yaml: :")
    
    manager = ConfigManager(config_path=config_file)
    assert manager.get("daemon_url") == "http://localhost:8443"
