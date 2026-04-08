"""
Property tests for database migrations.
Feature: architect-core-api-data-state
"""
import tempfile
from pathlib import Path

import pytest

from devready.daemon.migrations.manager import MigrationManager


@pytest.mark.asyncio
async def test_migrations_applied_automatically():
    """
    Feature: architect-core-api-data-state, Property 38: Migrations Applied Automatically
    Validates: Requirements 12.2
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        mgr = MigrationManager(db_path)
        await mgr.run()

        # DB file should exist and migration recorded
        assert Path(db_path).exists()

        # Running again should be idempotent (no error)
        await mgr.run()


@pytest.mark.asyncio
async def test_backup_created_before_migration():
    """
    Feature: architect-core-api-data-state, Property 39: Migration Backup Created Before Upgrade
    Validates: Requirements 12.3
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        # Pre-create the DB file so backup logic triggers
        db_path.write_bytes(b"")

        mgr = MigrationManager(str(db_path))
        backup_path = mgr._backup()

        assert backup_path is not None
        assert backup_path.exists()


@pytest.mark.asyncio
async def test_failed_migration_triggers_rollback(monkeypatch):
    """
    Feature: architect-core-api-data-state, Property 40: Failed Migration Triggers Rollback
    Validates: Requirements 12.4
    """
    import importlib
    import types

    import devready.daemon.migrations.manager as mgr_module

    async def bad_upgrade(session):
        raise RuntimeError("intentional failure")

    fake_mod = types.ModuleType("fake_module")
    fake_mod.upgrade = bad_upgrade  # type: ignore[attr-defined]

    monkeypatch.setattr(mgr_module, "_MIGRATIONS", [(99, "fake_module", "Bad migration")])
    monkeypatch.setattr(importlib, "import_module", lambda name: fake_mod)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Create a valid SQLite DB as the "original" so backup/restore works
        import aiosqlite
        async with aiosqlite.connect(str(db_path)) as conn:
            await conn.execute("CREATE TABLE marker (id INTEGER PRIMARY KEY)")
            await conn.commit()

        mgr = MigrationManager(str(db_path))
        with pytest.raises(RuntimeError, match="intentional failure"):
            await mgr.run()

        # DB should be restored from backup (backup file should exist)
        backup_path = db_path.with_suffix(".db.bak")
        assert backup_path.exists()
        # DB file should match the backup (restored)
        assert db_path.read_bytes() == backup_path.read_bytes()


@pytest.mark.asyncio
async def test_migration_operations_logged(caplog):
    """
    Feature: architect-core-api-data-state, Property 41: Migration Operations Are Logged
    Validates: Requirements 12.7
    """
    import logging

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")
        mgr = MigrationManager(db_path)

        with caplog.at_level(logging.INFO, logger="devready.daemon.migrations.manager"):
            await mgr.run()

        assert any("migration" in r.message.lower() or "Migration" in r.message for r in caplog.records)
