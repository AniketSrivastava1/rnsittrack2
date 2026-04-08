"""Database CRUD operations with retry logic for lock errors."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from devready.daemon.models import EnvironmentSnapshot

logger = logging.getLogger(__name__)

_RETRY_DELAYS = [0.1, 0.2, 0.4]  # exponential backoff in seconds


async def _retry(coro_fn, *args, **kwargs):
    """Retry a coroutine up to 3 times on OperationalError (DB lock)."""
    for attempt, delay in enumerate(_RETRY_DELAYS, 1):
        try:
            return await coro_fn(*args, **kwargs)
        except OperationalError as exc:
            logger.error("Database error (attempt %d/3): %s", attempt, exc)
            if attempt == len(_RETRY_DELAYS):
                raise
            await asyncio.sleep(delay)


async def insert_snapshot(session: AsyncSession, snapshot: EnvironmentSnapshot) -> EnvironmentSnapshot:
    async def _do():
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        return snapshot
    return await _retry(_do)


async def get_snapshot_by_id(session: AsyncSession, snapshot_id: str) -> Optional[EnvironmentSnapshot]:
    async def _do():
        result = await session.execute(select(EnvironmentSnapshot).where(EnvironmentSnapshot.id == snapshot_id))
        return result.scalar_one_or_none()
    return await _retry(_do)


async def list_snapshots(
    session: AsyncSession,
    project_path: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[EnvironmentSnapshot]:
    async def _do():
        stmt = select(EnvironmentSnapshot).order_by(EnvironmentSnapshot.timestamp.desc()).limit(limit).offset(offset)
        if project_path:
            stmt = stmt.where(EnvironmentSnapshot.project_path == project_path)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    return await _retry(_do)


async def get_latest_snapshot(session: AsyncSession, project_path: str) -> Optional[EnvironmentSnapshot]:
    async def _do():
        result = await session.execute(
            select(EnvironmentSnapshot)
            .where(EnvironmentSnapshot.project_path == project_path)
            .order_by(EnvironmentSnapshot.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    return await _retry(_do)


async def delete_snapshot(session: AsyncSession, snapshot_id: str) -> bool:
    async def _do():
        snap = await get_snapshot_by_id(session, snapshot_id)
        if snap is None:
            return False
        await session.delete(snap)
        await session.commit()
        return True
    return await _retry(_do)


async def delete_old_snapshots(session: AsyncSession, retention_days: int) -> int:
    """Delete snapshots older than retention_days. Returns count deleted."""
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    async def _do():
        result = await session.execute(
            delete(EnvironmentSnapshot).where(EnvironmentSnapshot.timestamp < cutoff)
        )
        await session.commit()
        return result.rowcount
    return await _retry(_do)


async def list_snapshots_history(
    session: AsyncSession,
    days: int = 30,
    project_path: Optional[str] = None,
    limit: int = 200,
) -> List[EnvironmentSnapshot]:
    """Return snapshots within the last `days` days, ordered ascending by timestamp."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    async def _do():
        stmt = (
            select(EnvironmentSnapshot)
            .where(EnvironmentSnapshot.timestamp >= cutoff)
            .order_by(EnvironmentSnapshot.timestamp.asc())
            .limit(min(limit, 1000))
        )
        if project_path:
            stmt = stmt.where(EnvironmentSnapshot.project_path == project_path)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    return await _retry(_do)


async def list_snapshots_history(
    session: AsyncSession,
    days: int = 30,
    project_path: Optional[str] = None,
    limit: int = 200,
) -> List[EnvironmentSnapshot]:
    """List snapshots within the last `days` days, optionally filtered by project_path."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    async def _do():
        stmt = (
            select(EnvironmentSnapshot)
            .where(EnvironmentSnapshot.timestamp >= cutoff)
            .order_by(EnvironmentSnapshot.timestamp.desc())
            .limit(limit)
        )
        if project_path:
            stmt = stmt.where(EnvironmentSnapshot.project_path == project_path)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    return await _retry(_do)
