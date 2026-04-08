"""API endpoints for environment fixes."""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from devready.daemon.database import get_session
from devready.daemon.models import PolicyViolation, TeamPolicy
from devready.daemon.services.fixer_service import FixerService, FixRecommendation, FixResult
from devready.daemon.services.snapshot_service import SnapshotService
from devready.daemon.services.drift_service import DriftDetectionService

router = APIRouter(prefix="/api/v1/fixes", tags=["fixes"])
_snapshot_svc = SnapshotService()
_drift_svc = DriftDetectionService()
_fixer_svc = FixerService()


class FixRecommendationRequest(BaseModel):
    snapshot_id: str
    team_policy: Optional[TeamPolicy] = None


@router.post("/recommendations", response_model=List[FixRecommendation])
async def get_recommendations(
    req: FixRecommendationRequest,
    session: AsyncSession = Depends(get_session),
) -> List[FixRecommendation]:
    """Provides recommendations for fixing policy violations in a snapshot."""
    snap = await _snapshot_svc.get_snapshot(session, req.snapshot_id)
    if snap is None:
        raise HTTPException(status_code=404, detail={
            "error_code": "SNAPSHOT_NOT_FOUND", "message": "No snapshot found", "details": {}})
    if not req.team_policy:
        return []
    violations = _drift_svc.check_policy_compliance(snap, req.team_policy)
    return _fixer_svc.get_recommendations(violations)


@router.post("/apply", response_model=FixResult)
async def apply_fix(recommendation: FixRecommendation) -> FixResult:
    """Applies a specific fix recommendation."""
    return await _fixer_svc.apply_fix(recommendation)
