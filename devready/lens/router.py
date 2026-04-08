"""Analytics FastAPI router — mounts into The Architect's daemon."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.database import get_session  # DEPENDS: shuvam/architect
from devready.daemon.db_operations import get_snapshot_by_id, list_snapshots_history
from devready.lens.aggregator import compute_compliance, compute_health_trend, compute_time_saved, compute_top_issues
from devready.lens.contract import ContractParseError, load_contract, validate_snapshot_against_contract
from devready.lens.models import ComplianceResponse, HealthTrendResponse, TimeSavedResponse, TopIssuesResponse

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics-lens"])


@router.get("/trends/health", response_model=HealthTrendResponse)
async def health_trend(
    project_path: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> HealthTrendResponse:
    snaps = await list_snapshots_history(session, days=days, project_path=project_path)
    entries, summary = compute_health_trend(snaps, days)
    return HealthTrendResponse(data=entries, summary=summary)


@router.get("/issues/top", response_model=TopIssuesResponse)
async def top_issues(
    project_path: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> TopIssuesResponse:
    snaps = await list_snapshots_history(session, days=days, project_path=project_path)
    return TopIssuesResponse(issues=compute_top_issues(snaps, limit=20))


@router.get("/time-saved", response_model=TimeSavedResponse)
async def time_saved(
    project_path: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> TimeSavedResponse:
    snaps = await list_snapshots_history(session, days=365, project_path=project_path)
    return compute_time_saved(snaps)


@router.get("/compliance", response_model=ComplianceResponse)
async def compliance(
    project_path: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> ComplianceResponse:
    snaps = await list_snapshots_history(session, days=30, project_path=project_path)
    threshold, contract_missing = 90, True
    if project_path:
        try:
            threshold = load_contract(project_path).min_health_score
            contract_missing = False
        except (FileNotFoundError, ContractParseError):
            pass
    score, compliant, total, top_violations = compute_compliance(snaps, threshold)
    return ComplianceResponse(compliance_score=round(score, 1), compliant_count=compliant,
                              total_count=total, violations_summary=top_violations, contract_missing=contract_missing)


@router.get("/contract")
async def get_contract(project_path: str = Query(...)):
    try:
        return {**load_contract(project_path).model_dump(), "api_version": "v1"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail={
            "error_code": "CONTRACT_NOT_FOUND", "message": f"No .devready.yml in {project_path}", "details": {}})
    except ContractParseError as e:
        raise HTTPException(status_code=400, detail={
            "error_code": "CONTRACT_INVALID", "message": str(e), "details": {}})


@router.post("/contract/validate")
async def validate_contract(snapshot_id: str = Query(...), session: AsyncSession = Depends(get_session)):
    snap = await get_snapshot_by_id(session, snapshot_id)
    if snap is None:
        raise HTTPException(status_code=404, detail={
            "error_code": "SNAPSHOT_NOT_FOUND", "message": f"Snapshot {snapshot_id} not found", "details": {}})
    try:
        contract = load_contract(snap.project_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail={
            "error_code": "CONTRACT_NOT_FOUND", "message": f"No .devready.yml in {snap.project_path}", "details": {}})
    except ContractParseError as e:
        raise HTTPException(status_code=400, detail={"error_code": "CONTRACT_INVALID", "message": str(e), "details": {}})
    violations = validate_snapshot_against_contract(snap, contract)
    return {"violations": [v.model_dump() for v in violations], "api_version": "v1"}
