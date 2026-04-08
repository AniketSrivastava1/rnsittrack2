"""Core Pydantic/SQLModel data models for DevReady Daemon."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field as SQLField


# ---------------------------------------------------------------------------
# Value objects (Pydantic only, not persisted as tables)
# ---------------------------------------------------------------------------

class ToolVersion(BaseModel):
    """Immutable representation of a single detected tool/runtime."""
    model_config = ConfigDict(frozen=True)

    name: str
    version: str
    path: str
    manager: Optional[str] = None


class VersionChange(BaseModel):
    tool_name: str
    old_version: str
    new_version: str
    severity: Literal["major", "minor", "patch"]


class ToolRequirement(BaseModel):
    name: str
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    allowed_managers: Optional[List[str]] = None


class EnvVarRequirement(BaseModel):
    name: str
    required: bool
    pattern: Optional[str] = None


class TeamPolicy(BaseModel):
    required_tools: List[ToolRequirement] = Field(default_factory=list)
    forbidden_tools: List[str] = Field(default_factory=list)
    version_constraints: Dict[str, str] = Field(default_factory=dict)
    env_var_requirements: List[EnvVarRequirement] = Field(default_factory=list)


class DriftReport(BaseModel):
    snapshot_a_id: str
    snapshot_b_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    added_tools: List[ToolVersion] = Field(default_factory=list)
    removed_tools: List[ToolVersion] = Field(default_factory=list)
    version_changes: List[VersionChange] = Field(default_factory=list)
    drift_score: int = Field(ge=0, le=100)


class PolicyViolation(BaseModel):
    violation_type: Literal["missing_tool", "version_mismatch", "forbidden_tool", "missing_env_var"]
    tool_or_var_name: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    severity: Literal["error", "warning"]
    message: str


# ---------------------------------------------------------------------------
# SQLModel table (persisted)
# ---------------------------------------------------------------------------

class EnvironmentSnapshot(SQLModel, table=True):
    """Primary entity for environment state, stored in SQLite."""
    __tablename__ = "environmentsnapshot"

    id: Optional[str] = SQLField(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True
    )
    timestamp: datetime = SQLField(default_factory=datetime.utcnow, index=True)
    project_path: str = SQLField(index=True)
    project_name: str
    tools: List[Dict[str, Any]] = SQLField(default_factory=list, sa_column=Column(JSON))
    dependencies: Dict[str, List[str]] = SQLField(default_factory=dict, sa_column=Column(JSON))
    env_vars: Dict[str, str] = SQLField(default_factory=dict, sa_column=Column(JSON))
    health_score: int = SQLField(ge=0, le=100)
    scan_duration_seconds: float
    violations: List[Dict[str, Any]] = SQLField(default_factory=list, sa_column=Column(JSON))


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class SnapshotCreateRequest(BaseModel):
    project_path: str
    project_name: str
    tools: List[ToolVersion] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    env_vars: Dict[str, str] = Field(default_factory=dict)
    scan_duration_seconds: float = 0.0
    team_policy: Optional[TeamPolicy] = None


class SnapshotResponse(BaseModel):
    snapshot_id: str
    timestamp: datetime
    project_path: str
    project_name: str
    tools: List[ToolVersion]
    dependencies: Dict[str, List[str]]
    env_vars: Dict[str, str]
    health_score: int
    scan_duration_seconds: float
    violations: List[PolicyViolation] = Field(default_factory=list)
    api_version: str = "v1"


class DriftCompareRequest(BaseModel):
    snapshot_a_id: str
    snapshot_b_id: str


class PolicyCheckRequest(BaseModel):
    snapshot_id: str
    team_policy: TeamPolicy


class MetricsResponse(BaseModel):
    cpu_percent: float
    memory_mb: float
    scan_count: int
    avg_scan_duration: float
    api_version: str = "v1"


class VersionResponse(BaseModel):
    api_version: str
    daemon_version: str
    build_number: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
