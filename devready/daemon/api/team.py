from fastapi import APIRouter, Depends, HTTPException
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from ..services.team_service import TeamSyncService
from ..models import EnvironmentSnapshot, TeamPolicy, ToolVersion, DriftReport, VersionChange
from ..services.drift_service import DriftDetectionService

router = APIRouter(prefix="/team", tags=["team"])

class TeamSummaryResponse(BaseModel):
    team_name: str
    aggregate_score: int
    member_count: int
    members: List[Dict[str, Any]]

class TeamSyncResponse(BaseModel):
    status: str
    last_sync: str

@router.get("/summary", response_model=TeamSummaryResponse)
async def get_team_summary():
    """Returns the aggregate health of the team."""
    service = TeamSyncService()
    return await service.get_team_health_summary()

@router.get("/members/{member_id}")
async def get_team_member_details(member_id: str):
    """Returns detailed history and setup for a specific teammate."""
    service = TeamSyncService()
    return await service.get_member_details(member_id)

@router.get("/drift", response_model=List[Dict[str, Any]])
async def get_team_drift():
    """Returns common drift items across the team."""
    service = TeamSyncService()
    return await service.get_drift_outliers()

@router.get("/compare/{member_id}", response_model=DriftReport)
async def compare_team_member(member_id: str, project_path: str = "."):
    """Returns a drift report comparing the current user with a teammate."""
    service = TeamSyncService()
    # In a real app, we'd fetch the latest local snapshot for project_path
    # For now, we craft a mock local snapshot
    local_snap = EnvironmentSnapshot(
        id="local-latest",
        project_path=project_path,
        project_name="devready",
        tools=[ToolVersion(name="python", version="3.11.0", path="/usr/bin/python", status="ok")],
        health_score=100,
        scan_duration_seconds=0.1
    )
    return await service.compare_with_member(local_snap, member_id)

@router.post("/sync", response_model=TeamSyncResponse)
async def sync_team_data():
    """Manual trigger to sync local snapshot with the hub."""
    service = TeamSyncService()
    # Logic to fetch latest local snapshot and sync...
    # For now, we simulate success
    return {
        "status": "success",
        "last_sync": "Just now"
    }
