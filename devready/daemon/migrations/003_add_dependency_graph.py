"""Migration 003: Add dependency_graph column to environmentsnapshot."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def upgrade(session: AsyncSession) -> None:
    # SQLite doesn't support IF NOT EXISTS for ADD COLUMN — check first
    try:
        await session.execute(text(
            "ALTER TABLE environmentsnapshot ADD COLUMN dependency_graph JSON DEFAULT '{}'"
        ))
    except Exception:
        pass  # column already exists


async def downgrade(session: AsyncSession) -> None:
    pass  # SQLite doesn't support DROP COLUMN in older versions
