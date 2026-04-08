"""Scan REST endpoints."""
from __future__ import annotations

import time
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.database import get_session
from devready.daemon.models import (
    SnapshotResponse,
    SnapshotCreateRequest,
    ToolVersion,
    TeamPolicy,
    PolicyViolation,
)
from devready.daemon.services.snapshot_service import SnapshotService
from devready.inspector.scan_orchestrator import ScanOrchestrator

router = APIRouter(prefix="/api/v1", tags=["scan"])
logger = logging.getLogger(__name__)

_snapshot_svc = SnapshotService()
_orchestrator = ScanOrchestrator()

class ScanRequest(BaseModel):
    project_path: Optional[str] = None
    scope: str = "full"
    ignore_tools: Optional[list[str]] = None
    ignore_deps: bool = False
    ignore_system: bool = False
    team_policy: Optional[TeamPolicy] = None

def _to_snapshot_response(snap) -> SnapshotResponse:
    # SQLModel JSON column returns list of dicts for violations
    violation_objects = []
    if snap.violations:
        for v in snap.violations:
            if isinstance(v, dict):
                violation_objects.append(PolicyViolation(**v))
            else:
                violation_objects.append(v)

    return SnapshotResponse(
        snapshot_id=snap.id,
        timestamp=snap.timestamp,
        project_path=snap.project_path,
        project_name=snap.project_name,
        tools=[ToolVersion(**t) for t in snap.tools],
        dependencies=snap.dependencies,
        env_vars=snap.env_vars,
        health_score=snap.health_score,
        scan_duration_seconds=snap.scan_duration_seconds,
        violations=violation_objects,
    )

@router.post("/scan")
async def perform_scan(
    req: ScanRequest,
    session: AsyncSession = Depends(get_session),
) -> SnapshotResponse:
    """Trigger an environment scan and return the resulting snapshot."""
    start_time = time.time()
    
    try:
        # 1. Run the inspector
        logger.info("Starting scan for project: %s", req.project_path)
        scan_result = _orchestrator.run_scan(
            project_path=req.project_path,
            scan_scope=req.scope
        )
        
        duration = time.time() - start_time
        
        # 2. Transform inspector data to match SnapshotCreateRequest
        # The inspector returns 'tools' as a dict of {name: version}
        # We need to convert it to a list of ToolVersion objects
        tools_dict = scan_result.get("tools", {})
        tools_list = []
        for name, version in tools_dict.items():
            if version:
                tools_list.append(ToolVersion(
                    name=name,
                    version=version,
                    path="unknown", # Path detection is limited in default tool detector
                    manager=None
                ))

        # 3. Create a snapshot persistence request
        create_req = SnapshotCreateRequest(
            project_path=scan_result.get("project_path", req.project_path or "."),
            project_name=scan_result.get("project_name", "unknown"),
            tools=tools_list,
            dependencies={"main": scan_result.get("dependencies", [])},
            env_vars=scan_result.get("env_vars", {}),
            scan_duration_seconds=duration,
            team_policy=req.team_policy
        )
        
        # 4. Save to database
        snap = await _snapshot_svc.create_snapshot(session, create_req)
        
        return _to_snapshot_response(snap)
        
    except Exception as e:
        logger.error("Scan failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "SCAN_FAILED",
                "message": f"Scan failed: {str(e)}",
                "details": {}
            }
        )
