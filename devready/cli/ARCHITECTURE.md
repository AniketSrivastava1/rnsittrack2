# Architecture: The Face (DevReady CLI)

This document outlines the technical design of the DevReady CLI and dashboard.

## Component Overview

### 1. Daemon Client (`daemon_client.py`)
- **Technology**: `httpx` (Async)
- **Responsibility**: Abstracting communication with the Architect Daemon.
- **Features**: Automatic retries with exponential backoff, error mapping to local exceptions.

### 2. Formatter (`formatter.py`)
- **Technology**: `Rich`
- **Responsibility**: Converting raw API data into terminal-ready layouts.
- **Components**: Panels, Tables, Progress bars, Theme supports for color blinding.

### 3. Dashboard (`dashboard.py`)
- **Technology**: `Textual`
- **Responsibility**: Full-terminal interactive experience.
- **Features**: Live WebSocket updates, reactive state management, asynchronous background tasks.

### 4. Output Routing (`output_handler.py`)
- **Responsibility**: Switching between human-friendly (Rich) and machine-friendly (JSON) modes.

### 5. Control Plane (`main.py`)
- **Technology**: `Typer`
- **Responsibility**: Command parsing, global flag management (`--verbose`, `--json`, etc.), orchestration.

## Error Handling
All Daemon communication errors are wrapped in a `DaemonError` hierarchy (see `errors.py`). The CLI ensures that any unhandled `DevReadyError` results in a clean error panel and exit code 1.

## Testing Strategy
- **Unit Tests**: Coverage for `ConfigManager`, `DaemonClient` (mocked), and `RichFormatter`.
- **Integration Tests**: Typer `CliRunner` tests for core command sequences.
- **UI Tests**: `Textual` pilot tests for dashboard interactivity.
- **Property Tests**: `Hypothesis` for validating JSON output invariance.
- **Performance Tests**: Startup time validation.
