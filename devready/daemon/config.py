"""Configuration management for DevReady Daemon."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARN", "WARNING", "ERROR"}
_DEFAULT_CONFIG_PATH = "~/.devready/config.yaml"


@dataclass
class DaemonConfig:
    host: str = "127.0.0.1"
    port: int = 8443
    workers: int = 1


@dataclass
class DatabaseConfig:
    path: str = "~/.devready/state.db"
    retention_days: int = 90
    backup_enabled: bool = True


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "~/.devready/logs/daemon.log"
    max_size_mb: int = 10
    backup_count: int = 5


@dataclass
class PerformanceConfig:
    max_concurrent_scans: int = 3
    request_timeout_seconds: int = 30
    rate_limit_per_minute: int = 100


@dataclass
class AppConfig:
    daemon: DaemonConfig = field(default_factory=DaemonConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)


def _default_yaml() -> str:
    return """\
daemon:
  host: "127.0.0.1"
  port: 8443
  workers: 1

database:
  path: "~/.devready/state.db"
  retention_days: 90
  backup_enabled: true

logging:
  level: "INFO"
  file: "~/.devready/logs/daemon.log"
  max_size_mb: 10
  backup_count: 5

performance:
  max_concurrent_scans: 3
  request_timeout_seconds: 30
  rate_limit_per_minute: 100
"""


def _validate(config: AppConfig) -> AppConfig:
    """Validate ranges; fall back to defaults for invalid values."""
    d = config.daemon
    if not (1 <= d.port <= 65535):
        logger.warning("Invalid port %d, using default 8443", d.port)
        d.port = 8443
    if d.workers < 1:
        d.workers = 1

    db = config.database
    if db.retention_days < 1:
        logger.warning("Invalid retention_days %d, using default 90", db.retention_days)
        db.retention_days = 90

    lg = config.logging
    if lg.level.upper() not in _VALID_LOG_LEVELS:
        logger.warning("Invalid log level '%s', using INFO", lg.level)
        lg.level = "INFO"
    if lg.max_size_mb < 1:
        lg.max_size_mb = 10
    if lg.backup_count < 0:
        lg.backup_count = 5

    perf = config.performance
    if perf.rate_limit_per_minute < 1:
        perf.rate_limit_per_minute = 100
    if perf.request_timeout_seconds < 1:
        perf.request_timeout_seconds = 30

    return config


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load config from YAML file, creating defaults if missing."""
    path = Path(config_path or _DEFAULT_CONFIG_PATH).expanduser()

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_default_yaml())
        logger.info("Created default config at %s", path)

    try:
        raw = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        logger.error("Invalid YAML in config file: %s — using defaults", exc)
        raw = {}

    cfg = AppConfig()

    d = raw.get("daemon", {})
    cfg.daemon = DaemonConfig(
        host=d.get("host", cfg.daemon.host),
        port=int(os.environ.get("DEVREADY_PORT", d.get("port", cfg.daemon.port))),
        workers=d.get("workers", cfg.daemon.workers),
    )

    db = raw.get("database", {})
    cfg.database = DatabaseConfig(
        path=db.get("path", cfg.database.path),
        retention_days=db.get("retention_days", cfg.database.retention_days),
        backup_enabled=db.get("backup_enabled", cfg.database.backup_enabled),
    )

    lg = raw.get("logging", {})
    cfg.logging = LoggingConfig(
        level=lg.get("level", cfg.logging.level),
        file=lg.get("file", cfg.logging.file),
        max_size_mb=lg.get("max_size_mb", cfg.logging.max_size_mb),
        backup_count=lg.get("backup_count", cfg.logging.backup_count),
    )

    perf = raw.get("performance", {})
    cfg.performance = PerformanceConfig(
        max_concurrent_scans=perf.get("max_concurrent_scans", cfg.performance.max_concurrent_scans),
        request_timeout_seconds=perf.get("request_timeout_seconds", cfg.performance.request_timeout_seconds),
        rate_limit_per_minute=perf.get("rate_limit_per_minute", cfg.performance.rate_limit_per_minute),
    )

    return _validate(cfg)
