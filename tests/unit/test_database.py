"""Unit tests for database operations."""
import pytest

from devready.daemon.db_operations import (
    delete_old_snapshots,
    delete_snapshot,
    get_latest_snapshot,
    get_snapshot_by_id,
    insert_snapshot,
    list_snapshots,
)
from tests.conftest import make_snapshot


@pytest.mark.asyncio
async def test_insert_and_get_snapshot(db_session):
    snap = make_snapshot()
    inserted = await insert_snapshot(db_session, snap)
    assert inserted.id is not None

    fetched = await get_snapshot_by_id(db_session, inserted.id)
    assert fetched is not None
    assert fetched.project_path == "/test/project"


@pytest.mark.asyncio
async def test_get_nonexistent_snapshot_returns_none(db_session):
    result = await get_snapshot_by_id(db_session, "nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_list_snapshots_filters_by_project(db_session):
    await insert_snapshot(db_session, make_snapshot(project_path="/proj/a"))
    await insert_snapshot(db_session, make_snapshot(project_path="/proj/b"))

    results = await list_snapshots(db_session, project_path="/proj/a")
    assert len(results) == 1
    assert results[0].project_path == "/proj/a"


@pytest.mark.asyncio
async def test_get_latest_snapshot(db_session):
    from datetime import datetime
    older = make_snapshot(project_path="/proj")
    older.timestamp = datetime(2020, 1, 1)
    newer = make_snapshot(project_path="/proj")
    newer.timestamp = datetime(2024, 1, 1)

    await insert_snapshot(db_session, older)
    await insert_snapshot(db_session, newer)

    latest = await get_latest_snapshot(db_session, "/proj")
    assert latest is not None
    assert latest.timestamp == datetime(2024, 1, 1)


@pytest.mark.asyncio
async def test_delete_snapshot(db_session):
    snap = await insert_snapshot(db_session, make_snapshot())
    deleted = await delete_snapshot(db_session, snap.id)
    assert deleted is True

    fetched = await get_snapshot_by_id(db_session, snap.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_nonexistent_snapshot_returns_false(db_session):
    result = await delete_snapshot(db_session, "no-such-id")
    assert result is False


@pytest.mark.asyncio
async def test_delete_old_snapshots(db_session):
    from datetime import datetime
    old = make_snapshot()
    old.timestamp = datetime(2000, 1, 1)
    recent = make_snapshot()

    await insert_snapshot(db_session, old)
    await insert_snapshot(db_session, recent)

    count = await delete_old_snapshots(db_session, retention_days=1)
    assert count == 1
