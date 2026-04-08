"""Snapshot REST endpoints."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.database import get_session
from devready.daemon.models import (
    SnapshotCreateRequest,
    SnapshotResponse,
    ToolVersion,
    PolicyViolation,
)
from devready.daemon.services.drift_service import DriftDetectionService
from devready.daemon.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/v1", tags=["snapshots"])
_snapshot_svc = SnapshotService()
_drift_svc = DriftDetectionService()


def _to_response(snap) -> SnapshotResponse:
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
        policy_violations=[PolicyViolation(**v) for v in (snap.policy_violations or [])],
    )


@router.post("/snapshots", status_code=201)
async def create_snapshot(
    req: SnapshotCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> SnapshotResponse:
    snap = await _snapshot_svc.create_snapshot(session, req)
    return _to_response(snap)


@router.get("/snapshots/latest")
async def get_latest_snapshot(
    project_path: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> SnapshotResponse:
    snap = await _snapshot_svc.get_latest_snapshot(session, project_path)
    if snap is None:
        raise HTTPException(status_code=404, detail={"error_code": "SNAPSHOT_NOT_FOUND", "message": "No snapshot found for project", "details": {}})
    return _to_response(snap)


@router.get("/snapshots/{snapshot_id}")
async def get_snapshot(
    snapshot_id: str,
    session: AsyncSession = Depends(get_session),
) -> SnapshotResponse:
    snap = await _snapshot_svc.get_snapshot(session, snapshot_id)
    if snap is None:
        raise HTTPException(status_code=404, detail={"error_code": "SNAPSHOT_NOT_FOUND", "message": f"Snapshot {snapshot_id} not found", "details": {"snapshot_id": snapshot_id}})
    return _to_response(snap)


@router.get("/snapshots")
async def list_snapshots(
    project_path: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> List[SnapshotResponse]:
    snaps = await _snapshot_svc.list_snapshots(session, project_path, limit, offset)
    return [_to_response(s) for s in snaps]


@router.delete("/snapshots/{snapshot_id}", status_code=204)
async def delete_snapshot(
    snapshot_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    deleted = await _snapshot_svc.delete_snapshot(session, snapshot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"error_code": "SNAPSHOT_NOT_FOUND", "message": f"Snapshot {snapshot_id} not found", "details": {}})
