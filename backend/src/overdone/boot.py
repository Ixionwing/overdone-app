from __future__ import annotations

import json

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from overdone.config import Settings
from overdone.ingest.catalog import seed_catalog
from overdone.models.exercise import Exercise


def _upgrade(connection: Connection, ini_path: str) -> None:
    cfg = Config(ini_path)
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


async def bootstrap_database(
    settings: Settings,
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not settings.bootstrap:
        return
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_conn: _upgrade(sync_conn, str(settings.resolved_alembic_ini()))
        )
    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(Exercise))
        if count:
            return
        path = settings.resolved_catalog_path()
        exercises = json.loads(path.read_text())
        if isinstance(exercises, dict):
            exercises = list(exercises.values())
        await seed_catalog(session, exercises)
        await session.commit()
