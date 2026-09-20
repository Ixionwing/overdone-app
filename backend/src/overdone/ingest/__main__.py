from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from overdone.config import settings
from overdone.db import create_engine, create_session_factory
from overdone.ingest.catalog import seed_catalog


async def _run(path: Path) -> int:
    exercises = json.loads(path.read_text())
    if isinstance(exercises, dict):
        exercises = list(exercises.values())
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)
    async with factory() as session:
        count = await seed_catalog(session, exercises)
        await session.commit()
    await engine.dispose()
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Overdone exercise catalog")
    parser.add_argument(
        "--path",
        type=Path,
        default=settings.resolved_catalog_path(),
    )
    args = parser.parse_args()
    count = asyncio.run(_run(args.path))
    print(f"seeded {count} exercises from {args.path}")


if __name__ == "__main__":
    main()
