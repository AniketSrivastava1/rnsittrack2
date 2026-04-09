"""Analytics endpoints — snapshot history and violations summary (Architect Req 16)."""
from __future__ import annotations

from collections import defaultdict
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.database import get_session
from devready.daemon.db_operations import list_snapshots_history
from devready.daemon.models import (
    PolicyViolation,
    SnapshotHistoryEntry,
    ViolationSummaryEntry,
    ViolationSummaryResponse,
)

router = APIRouter(prefix="/api/v1", tags=["analytics"])


def _violations(snap) -> List[PolicyViolation]:
    raw = getattr(snap, "policy_violations", None) or []
    try:
        return [PolicyViolation(**v) for v in raw]
    except Exception:
        return []


@router.get("/snapshots/history", response_model=List[SnapshotHistoryEntry])
async def get_snapshot_history(
    project_path: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(200, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> List[SnapshotHistoryEntry]:
    snaps = await list_snapshots_history(session, days=days, project_path=project_path, limit=limit)
    return [
        SnapshotHistoryEntry(
            id=s.id,
            timestamp=s.timestamp,
            health_score=s.health_score,
            scan_duration_seconds=s.scan_duration_seconds,
            tools=[{"name": t["name"], "version": t["version"]} for t in s.tools],
            policy_violations_count=len(_violations(s)),
        )
        for s in snaps
    ]


@router.get("/analytics/violations/summary", response_model=ViolationSummaryResponse)
async def get_violations_summary(
    project_path: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> ViolationSummaryResponse:
    snaps = await list_snapshots_history(session, days=days, project_path=project_path, limit=1000)
    counts: dict = defaultdict(lambda: {"count": 0, "last_seen": None})
    for snap in snaps:
        for v in _violations(snap):
            key = (v.violation_type, v.tool_or_var_name)
            counts[key]["count"] += 1
            if counts[key]["last_seen"] is None or snap.timestamp > counts[key]["last_seen"]:
                counts[key]["last_seen"] = snap.timestamp
    entries = [
        ViolationSummaryEntry(violation_type=k[0], tool_or_var_name=k[1],
                              count=v["count"], last_seen=v["last_seen"])
        for k, v in counts.items()
    ]
    entries.sort(key=lambda e: e.count, reverse=True)
    return ViolationSummaryResponse(violations=entries)
