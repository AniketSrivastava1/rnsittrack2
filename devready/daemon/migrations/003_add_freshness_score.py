"""Migration 003: Add freshness_score column to environmentsnapshot."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def upgrade(session: AsyncSession) -> None:
    try:
        await session.execute(text(
            "ALTER TABLE environmentsnapshot ADD COLUMN freshness_score REAL DEFAULT 100.0"
        ))
    except Exception:
        pass  # column already exists


async def downgrade(session: AsyncSession) -> None:
    pass
