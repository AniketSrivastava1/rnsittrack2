"""Migration 004: Add ai_configs column to environmentsnapshot."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def upgrade(session: AsyncSession) -> None:
    try:
        await session.execute(text(
            "ALTER TABLE environmentsnapshot ADD COLUMN ai_configs JSON DEFAULT '{}'"
        ))
    except Exception:
        pass


async def downgrade(session: AsyncSession) -> None:
    pass
