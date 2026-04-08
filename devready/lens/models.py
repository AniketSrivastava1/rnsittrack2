"""Pydantic response models for The Lens analytics layer."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class HealthTrendEntry(BaseModel):
    timestamp: datetime
    health_score: int
    snapshot_id: str


class HealthTrendSummary(BaseModel):
    current_score: Optional[int]
    score_7d_ago: Optional[int]
    score_30d_ago: Optional[int]
    trend_direction: Optional[Literal["improving", "degrading", "stable"]]


class HealthTrendResponse(BaseModel):
    data: List[HealthTrendEntry]
    summary: HealthTrendSummary
    api_version: str = "v1"


class IssueEntry(BaseModel):
    violation_type: str
    tool_or_var_name: str
    count: int
    last_seen: datetime
    severity: str


class TopIssuesResponse(BaseModel):
    issues: List[IssueEntry]
    api_version: str = "v1"


class TimeSavedBreakdownEntry(BaseModel):
    violation_type: str
    fix_count: int
    minutes_saved: int


class TimeSavedResponse(BaseModel):
    total_minutes_saved: int
    total_hours_saved: float
    fix_count: int
    breakdown_by_type: List[TimeSavedBreakdownEntry]
    api_version: str = "v1"


class ComplianceResponse(BaseModel):
    compliance_score: float
    compliant_count: int
    total_count: int
    violations_summary: List[IssueEntry]
    contract_missing: bool = False
    api_version: str = "v1"
