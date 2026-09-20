import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from overdone.db import create_engine, create_session_factory
from overdone.ingest.catalog import seed_catalog
from overdone.models.exercise import Exercise
from overdone.services.resolve import resolve_exercise_name, resolve_from_baseline

MINI = Path(__file__).resolve().parent / "fixtures" / "exercises_mini.json"


async def _seed(postgres_url: str) -> None:
    engine = create_engine(postgres_url)
    factory = create_session_factory(engine)
    async with factory() as session:
        await seed_catalog(session, json.loads(MINI.read_text()))
        await session.commit()
    await engine.dispose()


def test_resolve_exact_catalog_name(postgres_url: str) -> None:
    asyncio.run(_seed(postgres_url))

    async def run() -> str | None:
        engine = create_engine(postgres_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            found = await resolve_exercise_name(
                session, "Barbell Bench Press - Medium Grip"
            )
            bench = await session.scalar(
                select(Exercise).where(
                    Exercise.source_id == "Barbell_Bench_Press_-_Medium_Grip"
                )
            )
        await engine.dispose()
        assert bench is not None
        assert found == str(bench.id)
        return found

    assert asyncio.run(run())


def test_resolve_alias_db_bench(postgres_url: str) -> None:
    asyncio.run(_seed(postgres_url))

    async def run() -> str | None:
        engine = create_engine(postgres_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            found = await resolve_exercise_name(session, "DB Bench")
            bench = await session.scalar(
                select(Exercise).where(
                    Exercise.source_id == "Barbell_Bench_Press_-_Medium_Grip"
                )
            )
        await engine.dispose()
        assert bench is not None
        assert found == str(bench.id)
        return found

    assert asyncio.run(run())


def test_resolve_unknown_string_is_none(postgres_url: str) -> None:
    asyncio.run(_seed(postgres_url))

    async def run() -> str | None:
        engine = create_engine(postgres_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            found = await resolve_exercise_name(session, "zzzxnotanexercise999")
        await engine.dispose()
        return found

    assert asyncio.run(run()) is None


def test_resolve_embedding_nickname(postgres_url: str) -> None:
    asyncio.run(_seed(postgres_url))

    async def run() -> str | None:
        engine = create_engine(postgres_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            found = await resolve_exercise_name(session, "medium grip barbell bench")
            bench = await session.scalar(
                select(Exercise).where(
                    Exercise.source_id == "Barbell_Bench_Press_-_Medium_Grip"
                )
            )
        await engine.dispose()
        assert bench is not None
        assert found == str(bench.id)
        return found

    assert asyncio.run(run())


def test_stub_misses_medium_grip_nickname() -> None:
    names = ["Barbell Bench Press - Medium Grip"]
    assert resolve_from_baseline("medium grip barbell bench", names) is None
