"""Unit tests for configuration management."""
import tempfile
from pathlib import Path

import pytest

from devready.daemon.config import AppConfig, load_config


def test_load_creates_default_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = str(Path(tmpdir) / "config.yaml")
        cfg = load_config(cfg_path)
        assert cfg.daemon.port == 8443
        assert cfg.database.retention_days == 90
        assert Path(cfg_path).exists()


def test_load_invalid_yaml_uses_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = Path(tmpdir) / "config.yaml"
        cfg_path.write_text(": invalid: yaml: [[[")
        cfg = load_config(str(cfg_path))
        assert cfg.daemon.port == 8443


def test_invalid_port_falls_back_to_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = Path(tmpdir) / "config.yaml"
        cfg_path.write_text("daemon:\n  port: 99999\n")
        cfg = load_config(str(cfg_path))
        assert cfg.daemon.port == 8443


def test_invalid_log_level_falls_back():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = Path(tmpdir) / "config.yaml"
        cfg_path.write_text("logging:\n  level: VERBOSE\n")
        cfg = load_config(str(cfg_path))
        assert cfg.logging.level == "INFO"


def test_env_var_overrides_port(monkeypatch):
    monkeypatch.setenv("DEVREADY_PORT", "9000")
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = load_config(str(Path(tmpdir) / "config.yaml"))
        assert cfg.daemon.port == 9000
