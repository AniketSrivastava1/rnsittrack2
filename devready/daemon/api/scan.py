"""Scan REST endpoints."""
from __future__ import annotations

import asyncio
import os
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.database import get_session
from devready.daemon.models import SnapshotCreateRequest, SnapshotResponse, ToolVersion, PolicyViolation
from devready.daemon.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/v1", tags=["scan"])
_snapshot_svc = SnapshotService()


class ScanRequest(BaseModel):
    project_path: Optional[str] = None
    scope: str = "full"


@router.post("/scan")
async def scan_environment(
    req: ScanRequest = ScanRequest(),
    session: AsyncSession = Depends(get_session),
) -> SnapshotResponse:
    project_path = req.project_path or os.getcwd()

    # Run ScanOrchestrator in a thread (it uses ThreadPoolExecutor internally)
    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, _run_orchestrator, project_path, req.scope)

    # Map orchestrator tools dict → list of ToolVersion
    tools_raw = raw.get("tools", {})
    tools = [
        ToolVersion(name=name, version=ver or "unknown", path="", manager=None)
        for name, ver in tools_raw.items()
        if ver is not None
    ]

    # Map dependencies list → {lang: [pkg, ...]}
    deps_list = raw.get("dependencies", [])
    dependencies: dict[str, list[str]] = {}
    for dep in deps_list:
        lang = dep.get("type", "unknown")
        dependencies.setdefault(lang, []).append(dep.get("name", ""))

    env_vars = raw.get("env_vars", {})
    scan_duration = raw.get("performance", {}).get("total_seconds", 0.0)

    # Load policy from .devready-policy.yaml if present in project
    team_policy = _load_project_policy(project_path)

    snapshot_req = SnapshotCreateRequest(
        project_path=raw.get("project_path", project_path),
        project_name=raw.get("project_name", os.path.basename(project_path)),
        tools=tools,
        dependencies=dependencies,
        env_vars=env_vars,
        scan_duration_seconds=scan_duration,
        team_policy=team_policy,
    )

    snapshot = await _snapshot_svc.create_snapshot(session, snapshot_req)

    return SnapshotResponse(
        snapshot_id=snapshot.id,
        timestamp=snapshot.timestamp,
        project_path=snapshot.project_path,
        project_name=snapshot.project_name,
        tools=[ToolVersion(**t) for t in snapshot.tools],
        dependencies=snapshot.dependencies,
        env_vars=snapshot.env_vars,
        health_score=snapshot.health_score,
        scan_duration_seconds=snapshot.scan_duration_seconds,
        policy_violations=[PolicyViolation(**v) for v in (snapshot.policy_violations or [])],
    )


def _load_project_policy(project_path: str):
    """Load .devready-policy.yaml from project root if it exists."""
    import yaml
    from devready.daemon.models import TeamPolicy, ToolRequirement, EnvVarRequirement

    policy_file = os.path.join(project_path, ".devready-policy.yaml")
    if not os.path.exists(policy_file):
        return None
    try:
        with open(policy_file) as f:
            data = yaml.safe_load(f) or {}
        return TeamPolicy(
            required_tools=[ToolRequirement(**t) for t in data.get("required_tools", [])],
            forbidden_tools=data.get("forbidden_tools", []),
            env_var_requirements=[EnvVarRequirement(**e) for e in data.get("env_var_requirements", [])],
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Failed to load policy file: %s", e)
        return None


_SCOPE_MAP = {
    "full": "full",
    "system": "system_only",
    "dependencies": "dependencies_only",
    "configs": "configs_only",
}


def _run_orchestrator(project_path: str, scope: str) -> dict:
    from devready.inspector.scan_orchestrator import ScanOrchestrator
    return ScanOrchestrator().run_scan(project_path=project_path, scan_scope=_SCOPE_MAP.get(scope, "full"))
