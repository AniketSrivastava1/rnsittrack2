# DevReady Operator

The Operator component of DevReady manages isolated sandboxes, applies fixes to the environment, handles configuration, and enforces safety through dry-runs and rollbacks.

## Components
- **Docker Integration & Sandboxing:** Ephemeral environments for dry-running commands safely.
- **Risk Assessment:** Classifies fixes into local, user-global, and global scopes.
- **Git Hooks:** Intercepts project lifecycle events to auto-run DevReady checks and fixes.
- **Rollback:** Takes snapshots of configs and states before global fixes.
- **Package Adapters:** Supports Node.js, Python, Rust, Go, Java, and others.

## Setup
```bash
pip install -e .
```

## Testing
Run pytest for the suite:
```bash
pytest devready/operator/tests
```
