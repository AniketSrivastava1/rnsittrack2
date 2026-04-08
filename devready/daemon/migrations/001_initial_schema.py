"""Initial schema migration."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def upgrade(session: AsyncSession) -> None:
    await session.execute(  # type: ignore[arg-type]
        """
        CREATE TABLE IF NOT EXISTS environmentsnapshot (
            id TEXT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            project_path TEXT NOT NULL,
            project_name TEXT NOT NULL,
            tools JSON NOT NULL,
            dependencies JSON NOT NULL,
            env_vars JSON NOT NULL,
            health_score INTEGER NOT NULL CHECK(health_score >= 0 AND health_score <= 100),
            scan_duration_seconds REAL NOT NULL
        )
        """
    )
    await session.execute(  # type: ignore[arg-type]
        "CREATE INDEX IF NOT EXISTS idx_project_path ON environmentsnapshot(project_path)"
    )
    await session.execute(  # type: ignore[arg-type]
        "CREATE INDEX IF NOT EXISTS idx_timestamp ON environmentsnapshot(timestamp)"
    )


async def downgrade(session: AsyncSession) -> None:
    await session.execute("DROP TABLE IF EXISTS environmentsnapshot")  # type: ignore[arg-type]
