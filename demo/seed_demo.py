"""
Demo scenario: seed two snapshots into the daemon to simulate a non-compliant
environment and a drift between an old "good" state and the current "bad" state.

Usage:
    # Terminal 1 — start the daemon
    uvicorn devready.daemon.main:app --host 127.0.0.1 --port 8443

    # Terminal 2 — seed the demo data
    python demo/seed_demo.py

    # Then run CLI commands (see bottom of this file for the full walkthrough)
"""

import asyncio
import httpx
import json

BASE = "http://localhost:8443"
PROJECT = "/tmp/demo-project"

# ---------------------------------------------------------------------------
# Snapshot A — "last week's good state" (baseline)
# ---------------------------------------------------------------------------
SNAPSHOT_A = {
    "project_path": PROJECT,
    "project_name": "acme-backend",
    "scan_duration_seconds": 1.2,
    "tools": [
        {"name": "python",  "version": "3.12.2", "path": "/usr/bin/python3",   "manager": "system"},
        {"name": "node",    "version": "20.11.0", "path": "/usr/bin/node",      "manager": "nvm"},
        {"name": "docker",  "version": "25.0.3",  "path": "/usr/bin/docker",    "manager": "system"},
        {"name": "git",     "version": "2.44.0",  "path": "/usr/bin/git",       "manager": "system"},
        {"name": "poetry",  "version": "1.8.2",   "path": "/home/dev/.local/bin/poetry", "manager": "pip"},
    ],
    "dependencies": {
        "python": ["fastapi==0.110.0", "sqlalchemy==2.0.28", "pydantic==2.6.3", "httpx==0.27.0"],
        "node": ["typescript@5.4.2", "eslint@8.57.0"],
    },
    "env_vars": {
        "DATABASE_URL": "sqlite:///./dev.db",
        "LOG_LEVEL": "INFO",
        "NODE_ENV": "development",
    },
    "policy_violations": [],
}

# ---------------------------------------------------------------------------
# Snapshot B — "current broken state"
#
# What went wrong:
#   1. python downgraded to 3.10.x (project requires >=3.12)
#   2. node is missing entirely (someone removed nvm)
#   3. docker version is ancient (24.0.x, policy requires >=25)
#   4. DATABASE_URL env var is gone (misconfigured shell profile)
#   5. pydantic pinned to 1.x (incompatible with the codebase)
# ---------------------------------------------------------------------------
SNAPSHOT_B = {
    "project_path": PROJECT,
    "project_name": "acme-backend",
    "scan_duration_seconds": 1.8,
    "tools": [
        {"name": "python",  "version": "3.10.14", "path": "/usr/bin/python3",  "manager": "system"},
        # node is intentionally absent
        {"name": "docker",  "version": "24.0.9",  "path": "/usr/bin/docker",   "manager": "system"},
        {"name": "git",     "version": "2.44.0",  "path": "/usr/bin/git",      "manager": "system"},
        {"name": "poetry",  "version": "1.8.2",   "path": "/home/dev/.local/bin/poetry", "manager": "pip"},
    ],
    "dependencies": {
        "python": ["fastapi==0.110.0", "sqlalchemy==2.0.28", "pydantic==1.10.21", "httpx==0.27.0"],
        "node": [],  # node gone, no packages
    },
    "env_vars": {
        # DATABASE_URL intentionally missing
        "LOG_LEVEL": "DEBUG",
        "NODE_ENV": "development",
    },
    "policy_violations": [
        {
            "violation_type": "version_mismatch",
            "tool_or_var_name": "python",
            "expected": ">=3.12",
            "actual": "3.10.14",
            "severity": "error",
            "message": "Python 3.10.14 is below the required >=3.12. The project uses match-case syntax and 3.12 stdlib features.",
        },
        {
            "violation_type": "missing_tool",
            "tool_or_var_name": "node",
            "expected": ">=20.0.0",
            "actual": None,
            "severity": "error",
            "message": "Node.js is not installed. Frontend build and pre-commit hooks will fail.",
        },
        {
            "violation_type": "version_mismatch",
            "tool_or_var_name": "docker",
            "expected": ">=25.0.0",
            "actual": "24.0.9",
            "severity": "warning",
            "message": "Docker 24.0.9 is below the team-required >=25.0.0. Some compose features may not work.",
        },
        {
            "violation_type": "missing_env_var",
            "tool_or_var_name": "DATABASE_URL",
            "expected": "set",
            "actual": None,
            "severity": "error",
            "message": "DATABASE_URL is not set. The application will crash on startup.",
        },
    ],
}


async def seed():
    async with httpx.AsyncClient(base_url=BASE, timeout=10) as client:
        # Health check
        r = await client.get("/api/version")
        r.raise_for_status()
        print(f"Daemon running: {r.json()}\n")

        # POST snapshot A (baseline — good state)
        r = await client.post("/api/v1/snapshots", json=SNAPSHOT_A)
        r.raise_for_status()
        snap_a = r.json()
        snap_a_id = snap_a["snapshot_id"]
        print(f"[BASELINE] Snapshot A created  id={snap_a_id}  score={snap_a['health_score']}")

        # POST snapshot B (current — broken state)
        r = await client.post("/api/v1/snapshots", json=SNAPSHOT_B)
        r.raise_for_status()
        snap_b = r.json()
        snap_b_id = snap_b["snapshot_id"]
        print(f"[CURRENT]  Snapshot B created  id={snap_b_id}  score={snap_b['health_score']}")

        print("\n" + "=" * 60)
        print("DEMO WALKTHROUGH — run these commands in order:")
        print("=" * 60)
        print(f"\n# 1. Check current status (shows violations)")
        print(f"devready status --project {PROJECT}")
        print(f"\n# 2. View full scan result as JSON")
        print(f"devready scan --project {PROJECT} --json")
        print(f"\n# 3. Compare drift between good baseline and broken current state")
        print(f"devready drift --baseline {snap_a_id} --project {PROJECT}")
        print(f"\n# 4. View snapshot history")
        print(f"devready history --project {PROJECT}")
        print(f"\n# 5. See what fixes are recommended")
        print(f"devready fix --dry-run --project {PROJECT}")
        print(f"\n# 6. Direct API — inspect violations in detail")
        print(f"curl -s {BASE}/api/v1/snapshots/{snap_b_id} | python3 -m json.tool")
        print(f"\n# 7. Direct API — drift compare")
        print(f"""curl -s -X POST {BASE}/api/v1/drift/compare \\
  -H 'Content-Type: application/json' \\
  -d '{{"snapshot_a_id": "{snap_a_id}", "snapshot_b_id": "{snap_b_id}"}}' \\
  | python3 -m json.tool""")
        print()


if __name__ == "__main__":
    asyncio.run(seed())
