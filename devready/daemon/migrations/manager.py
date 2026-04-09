"""Database migration manager."""
from __future__ import annotations

import importlib
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

logger = logging.getLogger(__name__)

_MIGRATIONS = [
    (1, "devready.daemon.migrations.001_initial_schema", "Initial schema"),
    (2, "devready.daemon.migrations.002_add_policy_violations", "Add policy_violations column"),
    (3, "devready.daemon.migrations.003_add_freshness_score", "Add freshness_score column"),
    (4, "devready.daemon.migrations.004_add_ai_configs", "Add ai_configs column"),
]


class MigrationManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path).expanduser()

    async def run(self) -> None:
        """Detect and apply pending migrations."""
        engine = create_async_engine(f"sqlite+aiosqlite:///{self.db_path}", echo=False)
        async with engine.begin() as conn:
            await conn.execute(text(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at DATETIME NOT NULL, description TEXT NOT NULL)"
            ))

        async with AsyncSession(engine, expire_on_commit=False) as session:
            applied = await self._get_applied_versions(session)
            pending = [(v, mod, desc) for v, mod, desc in _MIGRATIONS if v not in applied]

            if not pending:
                logger.info("No pending migrations")
                await engine.dispose()
                return

            backup_path = self._backup()
            try:
                for version, module_name, description in pending:
                    logger.info("Applying migration %d: %s", version, description)
                    module = importlib.import_module(module_name)
                    await module.upgrade(session)
                    await session.execute(text(
                        "INSERT INTO schema_migrations (version, applied_at, description) VALUES (:v, :t, :d)"
                    ), {"v": version, "t": datetime.utcnow().isoformat(), "d": description})
                    await session.commit()
                    logger.info("Migration %d applied successfully", version)
            except Exception as exc:
                logger.error("Migration failed: %s — restoring backup", exc, exc_info=True)
                await engine.dispose()
                if backup_path and backup_path.exists():
                    shutil.copy2(str(backup_path), str(self.db_path))
                    logger.info("Database restored from backup")
                raise

        await engine.dispose()

    async def _get_applied_versions(self, session: AsyncSession) -> List[int]:
        result = await session.execute(text("SELECT version FROM schema_migrations"))
        return [row[0] for row in result.fetchall()]

    def _backup(self) -> Path | None:
        if not self.db_path.exists():
            return None
        backup = self.db_path.with_suffix(".db.bak")
        shutil.copy2(str(self.db_path), str(backup))
        logger.info("Database backed up to %s", backup)
        return backup
