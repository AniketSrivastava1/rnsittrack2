"""Shared pytest fixtures."""
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

import devready.daemon.database as db_module
from devready.daemon.models import EnvironmentSnapshot


@pytest_asyncio.fixture
async def db_session():
    """In-memory SQLite session for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Patch the global engine so get_session() uses in-memory DB
    db_module._engine = engine

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    await engine.dispose()
    db_module._engine = None


@pytest_asyncio.fixture
async def test_client(db_session):
    """FastAPI test client with in-memory DB."""
    from devready.daemon.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


def make_snapshot(**kwargs) -> EnvironmentSnapshot:
    defaults = dict(
        project_path="/test/project",
        project_name="test-project",
        tools=[],
        dependencies={},
        env_vars={},
        health_score=80,
        scan_duration_seconds=1.0,
    )
    defaults.update(kwargs)
    return EnvironmentSnapshot(**defaults)
