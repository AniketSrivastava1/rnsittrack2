# DevReady CLI - The Face

Modern, delightful interface for environment health monitoring.

## Features
- **Typer CLI**: Intuitive subcommands for scanning, fixing, and drifting.
- **Rich Output**: Beautiful terminal panels, tables, and progress indicators.
- **Textual Dashboard**: Interactive live TUI for real-time monitoring.
- **CI/CD Friendly**: Automatic TTY detection and JSON output modes.

## Installation
```bash
pip install -e .
```

## Usage

### Scan
Scan your environment for issues:
```bash
devready scan
```

### Fix
Apply recommended fixes:
```bash
devready fix --yes
```

### Dashboard
Launch the interactive dashboard:
```bash
devready dashboard
```

### JSON Mode
Output results for automation:
```bash
devready --json scan
```

## Commands
- `scan`: Run environment diagnostics.
- `fix`: Apply automated remediations.
- `status`: Show latest scan result.
- `drift`: Compare current state against baseline or policy.
- `snapshot`: Manage environment state snapshots.
- `team`: Sync policies and status with your team.
- `daemon`: Control the background architect.

## Development
See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details.
