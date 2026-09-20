import asyncio
import json
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from overdone.db import create_engine, create_session_factory
from overdone.ingest.catalog import seed_catalog
from overdone.models.embeddings import DataEmbedding
from overdone.models.exercise import Exercise, ExerciseAlias, ExerciseEnrichment

MINI = Path(__file__).resolve().parent / "fixtures" / "exercises_mini.json"


async def _wipe_catalog(session: AsyncSession) -> None:
    await session.execute(
        text(
            "TRUNCATE TABLE data_embeddings, exercise_aliases, "
            "exercise_enrichment, exercises RESTART IDENTITY CASCADE"
        )
    )


def test_seed_catalog_is_idempotent_and_384d(postgres_url: str) -> None:
    exercises = json.loads(MINI.read_text())

    async def run() -> tuple[int, int, int, int, int]:
        engine = create_engine(postgres_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            await _wipe_catalog(session)
            await session.commit()
        async with factory() as session:
            first = await seed_catalog(session, exercises)
            await session.commit()
        async with factory() as session:
            second = await seed_catalog(session, exercises)
            await session.commit()
            exercise_count = await session.scalar(
                select(func.count()).select_from(Exercise)
            )
            chunk_count = await session.scalar(
                select(func.count()).select_from(DataEmbedding)
            )
            alias_count = await session.scalar(
                select(func.count()).select_from(ExerciseAlias)
            )
            dim = await session.scalar(
                select(func.vector_dims(DataEmbedding.embedding)).limit(1)
            )
            bench = await session.scalar(
                select(Exercise).where(
                    Exercise.source_id == "Barbell_Bench_Press_-_Medium_Grip"
                )
            )
            enrich = await session.get(ExerciseEnrichment, bench.id) if bench else None
        await engine.dispose()
        assert bench is not None
        assert enrich is not None
        assert enrich.cns_factor == 0.85
        assert enrich.joints["shoulder"] > 0
        assert alias_count and alias_count >= 5
        return (
            first,
            second,
            int(exercise_count or 0),
            int(chunk_count or 0),
            int(dim or 0),
        )

    first, second, exercise_count, chunk_count, dim = asyncio.run(run())
    assert first == 5
    assert second == 5
    assert exercise_count == 5
    assert chunk_count == 5
    assert dim == 384
