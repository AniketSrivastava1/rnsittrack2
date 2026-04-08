"""Drift detection REST endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.database import get_session
from devready.daemon.models import DriftCompareRequest, DriftReport, PolicyCheckRequest, PolicyViolation
from devready.daemon.services.drift_service import DriftDetectionService
from devready.daemon.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/v1/drift", tags=["drift"])
_snapshot_svc = SnapshotService()
_drift_svc = DriftDetectionService()


@router.post("/compare")
async def compare_snapshots(
    req: DriftCompareRequest,
    session: AsyncSession = Depends(get_session),
) -> DriftReport:
    snap_a = await _snapshot_svc.get_snapshot(session, req.snapshot_a_id)
    snap_b = await _snapshot_svc.get_snapshot(session, req.snapshot_b_id)
    if snap_a is None:
        raise HTTPException(status_code=404, detail={"error_code": "SNAPSHOT_NOT_FOUND", "message": f"Snapshot {req.snapshot_a_id} not found", "details": {}})
    if snap_b is None:
        raise HTTPException(status_code=404, detail={"error_code": "SNAPSHOT_NOT_FOUND", "message": f"Snapshot {req.snapshot_b_id} not found", "details": {}})
    return _drift_svc.compare_snapshots(snap_a, snap_b)


@router.post("/policy")
async def check_policy(
    req: PolicyCheckRequest,
    session: AsyncSession = Depends(get_session),
) -> List[PolicyViolation]:
    snap = await _snapshot_svc.get_snapshot(session, req.snapshot_id)
    if snap is None:
        raise HTTPException(status_code=404, detail={"error_code": "SNAPSHOT_NOT_FOUND", "message": f"Snapshot {req.snapshot_id} not found", "details": {}})
    return _drift_svc.check_policy_compliance(snap, req.team_policy)
