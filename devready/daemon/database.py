"""Async SQLite database engine and session management."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)

_engine = None


def get_engine(db_path: str = "~/.devready/state.db"):
    global _engine
    if _engine is None:
        resolved = str(Path(db_path).expanduser())
        Path(resolved).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_async_engine(
            f"sqlite+aiosqlite:///{resolved}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return _engine


async def init_db(db_path: str = "~/.devready/state.db") -> None:
    """Create all tables if they don't exist."""
    engine = get_engine(db_path)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database initialized at %s", db_path)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection: yields an async DB session."""
    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def close_engine() -> None:
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
