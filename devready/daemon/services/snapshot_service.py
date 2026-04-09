"""Snapshot service - orchestrates snapshot creation and retrieval."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.context import ContextDetector
from devready.daemon.db_operations import (
    delete_old_snapshots,
    delete_snapshot,
    get_latest_snapshot,
    get_snapshot_by_id,
    insert_snapshot,
    list_snapshots,
)
from devready.daemon.models import EnvironmentSnapshot, SnapshotCreateRequest
from devready.daemon.services.drift_service import DriftDetectionService
from devready.daemon.services.health_calculator import HealthScoreCalculator

_context_detector = ContextDetector()
_health_calc = HealthScoreCalculator()
_drift_svc = DriftDetectionService()


class SnapshotService:
    async def create_snapshot(
        self, session: AsyncSession, req: SnapshotCreateRequest
    ) -> EnvironmentSnapshot:
        project_path, detected_name = _context_detector.detect(req.project_path)
        project_name = req.project_name or detected_name

        tools_data = [t.model_dump() for t in req.tools]

        temp_snap = EnvironmentSnapshot(
            project_path=project_path,
            project_name=project_name,
            tools=tools_data,
            dependencies=req.dependencies,
            env_vars=req.env_vars,
            health_score=0,
            scan_duration_seconds=req.scan_duration_seconds,
            freshness_score=req.freshness_score,
            ai_configs=req.ai_configs,
            dependency_graph=req.dependency_graph.model_dump() if req.dependency_graph else {},
        )

        # Generate violations from policy if provided, then merge with any caller-supplied ones
        if req.team_policy:
            policy_violations = _drift_svc.check_policy_compliance(temp_snap, req.team_policy)
            # Merge: add caller-supplied violations not already covered by policy check
            existing_keys = {(v.violation_type, v.tool_or_var_name) for v in policy_violations}
            for v in req.policy_violations:
                if (v.violation_type, v.tool_or_var_name) not in existing_keys:
                    policy_violations.append(v)
            violations = policy_violations
        else:
            violations = list(req.policy_violations)

        health_score = _health_calc.calculate_score(temp_snap, req.team_policy)

        snapshot = EnvironmentSnapshot(
            project_path=project_path,
            project_name=project_name,
            tools=tools_data,
            dependencies=req.dependencies,
            env_vars=req.env_vars,
            health_score=health_score,
            scan_duration_seconds=req.scan_duration_seconds,
            freshness_score=req.freshness_score,
            ai_configs=req.ai_configs,
            policy_violations=[v.model_dump() for v in violations],
            dependency_graph=req.dependency_graph.model_dump() if req.dependency_graph else {},
        )
        return await insert_snapshot(session, snapshot)

    async def get_snapshot(self, session: AsyncSession, snapshot_id: str) -> Optional[EnvironmentSnapshot]:
        return await get_snapshot_by_id(session, snapshot_id)

    async def list_snapshots(
        self, session: AsyncSession, project_path: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[EnvironmentSnapshot]:
        return await list_snapshots(session, project_path, limit, offset)

    async def get_latest_snapshot(self, session: AsyncSession, project_path: str) -> Optional[EnvironmentSnapshot]:
        return await get_latest_snapshot(session, project_path)

    async def delete_snapshot(self, session: AsyncSession, snapshot_id: str) -> bool:
        return await delete_snapshot(session, snapshot_id)

    async def cleanup_old_snapshots(self, session: AsyncSession, retention_days: int) -> int:
        return await delete_old_snapshots(session, retention_days)
