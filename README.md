# DevReady Daemon

The Architect component — a FastAPI daemon that serves as the single source of truth for environment state management in DevReady CLI.

## Overview

Runs locally on `localhost:8443`, providing REST and WebSocket APIs for:
- Environment snapshot management
- Drift detection between snapshots
- Policy compliance checking
- Real-time scan progress via WebSocket
- Performance metrics

## Requirements

- Python 3.11+
- No external services required (100% local-first, SQLite)

## Setup

```bash
pip install -e ".[dev]"
```

## Running

```bash
uvicorn devready.daemon.main:app --host 127.0.0.1 --port 8443
```

API docs available at: `http://localhost:8443/api/docs`

## Configuration

Config file: `~/.devready/config.yaml` (auto-created with defaults on first run)

```yaml
daemon:
  host: "127.0.0.1"
  port: 8443

database:
  path: "~/.devready/state.db"
  retention_days: 90

logging:
  level: "INFO"
  file: "~/.devready/logs/daemon.log"

performance:
  rate_limit_per_minute: 100
  request_timeout_seconds: 30
```

Environment variable overrides: `DEVREADY_PORT`

## API Endpoints

### Snapshots
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/snapshots` | Create snapshot (201) |
| GET | `/api/v1/snapshots/{id}` | Get by ID (200/404) |
| GET | `/api/v1/snapshots?project_path=...` | List for project |
| GET | `/api/v1/snapshots/latest?project_path=...` | Most recent |
| DELETE | `/api/v1/snapshots/{id}` | Delete (204/404) |

### Drift
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/drift/compare` | Compare two snapshots |
| POST | `/api/v1/drift/policy` | Check policy compliance |

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/metrics` | CPU, memory, scan stats |
| GET | `/api/version` | API version info |

### WebSocket
- `ws://localhost:8443/ws/scan?project_path=/path/to/project`

## Testing

```bash
# All tests
python -m pytest tests/

# Unit tests only
python -m pytest tests/unit/

# Property-based tests
python -m pytest tests/property/

# Integration tests
python -m pytest tests/integration/
```

## Architecture

```
devready/daemon/
├── main.py              # FastAPI app, middleware, startup/shutdown
├── models.py            # Pydantic/SQLModel data models
├── database.py          # Async SQLite engine and session
├── db_operations.py     # CRUD operations with retry logic
├── config.py            # Configuration management
├── context.py           # Project context detection
├── logging_config.py    # Rotating file logging with redaction
├── api/
│   ├── snapshots.py     # Snapshot REST endpoints
│   ├── drift.py         # Drift detection endpoints
│   ├── system.py        # Metrics and version endpoints
│   └── websocket.py     # WebSocket endpoint
├── services/
│   ├── snapshot_service.py    # Snapshot business logic
│   ├── health_calculator.py   # Health score computation
│   ├── drift_service.py       # Drift detection logic
│   └── metrics_collector.py   # Background metrics collection
├── middleware/
│   ├── rate_limit.py    # 100 req/min rate limiting
│   └── security.py      # Path sanitization, size limits
├── websocket/
│   └── manager.py       # WebSocket connection registry
└── migrations/
    ├── manager.py        # Migration runner with backup/rollback
    └── 001_initial_schema.py
```

## Error Response Format

All errors return:
```json
{
  "error_code": "SNAPSHOT_NOT_FOUND",
  "message": "Snapshot with id abc123 does not exist",
  "details": {}
}
```
