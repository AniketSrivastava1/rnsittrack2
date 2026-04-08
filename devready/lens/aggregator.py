"""Pure aggregation functions — no DB access, no side effects."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple

from devready.lens.models import (
    HealthTrendEntry,
    HealthTrendSummary,
    IssueEntry,
    TimeSavedBreakdownEntry,
    TimeSavedResponse,
)

_TIME_SAVED_TABLE: Dict[str, int] = {
    "missing_tool": 30,
    "version_mismatch": 20,
    "missing_env_var": 25,
    "forbidden_tool": 10,
}


def _violations_from_snap(snap: Any) -> List[Dict]:
    raw = getattr(snap, "policy_violations", None) or []
    return raw if isinstance(raw, list) else []


def _trend_direction(current: Optional[int], week_ago: Optional[int]) -> Literal["improving", "degrading", "stable"]:
    if current is None or week_ago is None:
        return "stable"
    if current > week_ago + 2:
        return "improving"
    if current < week_ago - 2:
        return "degrading"
    return "stable"


def compute_health_trend(snapshots: List[Any], days: int = 30) -> Tuple[List[HealthTrendEntry], HealthTrendSummary]:
    now = datetime.utcnow()
    cutoff_7d = now - timedelta(days=7)

    entries = [HealthTrendEntry(timestamp=s.timestamp, health_score=s.health_score, snapshot_id=s.id)
               for s in snapshots]

    current_score = snapshots[-1].health_score if snapshots else None
    score_7d = next((s.health_score for s in reversed(snapshots) if s.timestamp <= cutoff_7d + timedelta(hours=1)), None)
    score_30d = snapshots[0].health_score if snapshots else None

    summary = HealthTrendSummary(
        current_score=current_score,
        score_7d_ago=score_7d,
        score_30d_ago=score_30d,
        trend_direction=_trend_direction(current_score, score_7d) if snapshots else None,
    )
    return entries, summary


def compute_top_issues(snapshots: List[Any], limit: int = 20) -> List[IssueEntry]:
    counts: Dict[tuple, Dict] = defaultdict(lambda: {"count": 0, "last_seen": None, "severity": "warning"})
    for snap in snapshots:
        for v in _violations_from_snap(snap):
            key = (v.get("violation_type", ""), v.get("tool_or_var_name", ""))
            counts[key]["count"] += 1
            counts[key]["severity"] = v.get("severity", "warning")
            if counts[key]["last_seen"] is None or snap.timestamp > counts[key]["last_seen"]:
                counts[key]["last_seen"] = snap.timestamp
    entries = [
        IssueEntry(violation_type=k[0], tool_or_var_name=k[1],
                   count=v["count"], last_seen=v["last_seen"] or datetime.utcnow(), severity=v["severity"])
        for k, v in counts.items()
    ]
    entries.sort(key=lambda e: e.count, reverse=True)
    return entries[:limit]


def compute_time_saved(snapshots: List[Any]) -> TimeSavedResponse:
    fix_counts: Dict[str, int] = defaultdict(int)
    for i in range(len(snapshots) - 1):
        curr = {(v.get("violation_type"), v.get("tool_or_var_name")) for v in _violations_from_snap(snapshots[i])}
        nxt = {(v.get("violation_type"), v.get("tool_or_var_name")) for v in _violations_from_snap(snapshots[i + 1])}
        for vtype, _ in curr - nxt:
            if vtype:
                fix_counts[vtype] += 1
    breakdown = [
        TimeSavedBreakdownEntry(violation_type=vtype, fix_count=count,
                                minutes_saved=count * _TIME_SAVED_TABLE.get(vtype, 15))
        for vtype, count in fix_counts.items()
    ]
    total_minutes = sum(b.minutes_saved for b in breakdown)
    return TimeSavedResponse(
        total_minutes_saved=total_minutes,
        total_hours_saved=round(total_minutes / 60, 1),
        fix_count=sum(b.fix_count for b in breakdown),
        breakdown_by_type=breakdown,
    )


def compute_compliance(snapshots: List[Any], threshold: int = 90) -> Tuple[float, int, int, List[IssueEntry]]:
    latest: Dict[str, Any] = {}
    for snap in snapshots:
        if snap.project_path not in latest or snap.timestamp > latest[snap.project_path].timestamp:
            latest[snap.project_path] = snap
    snaps = list(latest.values())
    total = len(snaps)
    compliant = sum(1 for s in snaps if s.health_score >= threshold)
    score = (compliant / total * 100) if total > 0 else 0.0
    return score, compliant, total, compute_top_issues(snaps, limit=5)
