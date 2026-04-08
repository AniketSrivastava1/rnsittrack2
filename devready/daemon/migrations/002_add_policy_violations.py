"""Migration 002: Add policy_violations column to environmentsnapshot."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def upgrade(session: AsyncSession) -> None:
    # SQLite doesn't support IF NOT EXISTS for ADD COLUMN — check first
    from sqlalchemy import text, inspect
    try:
        await session.execute(text(
            "ALTER TABLE environmentsnapshot ADD COLUMN policy_violations JSON DEFAULT '[]'"
        ))
    except Exception:
        pass  # column already exists


async def downgrade(session: AsyncSession) -> None:
    pass  # SQLite doesn't support DROP COLUMN in older versions
