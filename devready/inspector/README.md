# DevReady Inspector

The Inspector is the scanning and intelligence layer of the DevReady environment health monitor. It collects system data, identifies tools and versions, analyzes project dependencies, and validates everything against team policies.

## Features

- **Fast & Parallel Scanning:** Full environment scans in under 2 seconds using multi-threading.
- **System Analysis:** Uses `osquery` to query installed packages, listening ports, and OS metadata.
- **Dependency Insights:** Integrates with `Syft` to generate SBOMs and identify outdated/vulnerable packages.
- **AI Agent Support:** Automatically detects and parses `CLAUDE.md`, `.cursorrules`, and other agent config files.
- **Privacy First:** Mandatory redaction of sensitive environment variables and secrets.
- **Extensible Architecture:** Modular scanners with a unified `ScanOrchestrator` and `Pydantic` validation.

## Architecture

1. **Subprocess Wrapper:** Secure command execution with timeout and sanitization.
2. **Scanners:** Individual modules for System, Tools, Stack, and Dependencies.
3. **Parsers:** Intelligent parsers for SBOM output and AI agent configs.
4. **Intelligence:** Policy checking and freshness analysis.
5. **Orchestration:** High-level engine with caching and performance monitoring.

## Development

### Prerequisites
- Python 3.14+
- `osquery` (optional, for system scans)
- `syft` (optional, for dependency scans)

### Installation
```bash
pip install -e .
```

### Running Tests
```bash
pytest devready/inspector/tests/
```

### Manual Scan
```python
from devready.inspector.scan_orchestrator import ScanOrchestrator
orchestrator = ScanOrchestrator()
result = orchestrator.run_scan(project_path=".")
print(result)
```
