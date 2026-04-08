"""Fix recommendation and application endpoints."""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.database import get_session
from devready.daemon.db_operations import get_latest_snapshot, get_snapshot_by_id
from devready.daemon.models import (
    FixApplyRequest,
    FixApplyResponse,
    FixRecommendation,
    FixResult,
    PolicyViolation,
)

router = APIRouter(prefix="/api/v1", tags=["fixes"])

# Ephemeral in-memory store of pending fixes keyed by fix_id (reset on daemon restart)
_pending_fixes: dict[str, FixRecommendation] = {}

_TIME_ESTIMATES = {"missing_tool": 30, "version_mismatch": 20, "missing_env_var": 25, "forbidden_tool": 10}


def _violation_to_fix(v: PolicyViolation) -> FixRecommendation:
    commands = {
        "missing_tool": f"mise install {v.tool_or_var_name}" + (f"@{v.expected}" if v.expected else ""),
        "version_mismatch": f"mise use {v.tool_or_var_name}@{v.expected or 'latest'}",
        "forbidden_tool": f"# Remove {v.tool_or_var_name} from your environment",
        "missing_env_var": f"export {v.tool_or_var_name}=<value>",
    }
    return FixRecommendation(
        fix_id=str(uuid.uuid4()),
        issue_description=v.message,
        command=commands.get(v.violation_type),
        confidence="high" if v.violation_type in ("missing_tool", "version_mismatch") else "medium",
        estimated_minutes=_TIME_ESTIMATES.get(v.violation_type, 15),
        affects_global=v.violation_type in ("missing_tool", "version_mismatch"),
        violation=v,
    )


@router.get("/fixes", response_model=List[FixRecommendation])
async def get_fix_recommendations(
    project_path: Optional[str] = Query(None),
    snapshot_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> List[FixRecommendation]:
    if snapshot_id:
        snap = await get_snapshot_by_id(session, snapshot_id)
    elif project_path:
        snap = await get_latest_snapshot(session, project_path)
    else:
        raise HTTPException(status_code=422, detail={
            "error_code": "MISSING_PARAM", "message": "Provide project_path or snapshot_id", "details": {}})
    if snap is None:
        raise HTTPException(status_code=404, detail={
            "error_code": "SNAPSHOT_NOT_FOUND", "message": "No snapshot found", "details": {}})

    violations = []
    for v in (getattr(snap, "policy_violations", None) or []):
        try:
            violations.append(PolicyViolation(**v))
        except Exception:
            continue

    fixes = [_violation_to_fix(v) for v in violations]
    for fix in fixes:
        _pending_fixes[fix.fix_id] = fix
    return fixes


@router.post("/fixes/apply", response_model=FixApplyResponse)
async def apply_fixes(req: FixApplyRequest) -> FixApplyResponse:
    results: List[FixResult] = []
    for fix_id in req.fix_ids:
        fix = _pending_fixes.get(fix_id)
        if fix is None:
            results.append(FixResult(fix_id=fix_id, success=False, message="Fix not found or expired"))
            continue
        if req.dry_run:
            results.append(FixResult(fix_id=fix_id, success=True,
                message=f"[dry-run] Would run: {fix.command or fix.manual_steps or 'manual fix required'}"))
        else:
            results.append(FixResult(fix_id=fix_id, success=True,
                message=f"Fix queued for Operator: {fix.command or 'manual'}"))
    return FixApplyResponse(results=results)
