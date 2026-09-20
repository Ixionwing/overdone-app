import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from overdone.db import create_engine, create_session_factory
from overdone.ingest.catalog import seed_catalog
from overdone.models.exercise import Exercise
from overdone.schemas.api import BaselineImport
from overdone.services.baseline import replace_baseline
from overdone.services.retrieve import retrieve_context

MINI = Path(__file__).resolve().parent / "fixtures" / "exercises_mini.json"
SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample_baseline.json"


def test_retrieve_exercise_includes_source_id(postgres_url: str) -> None:
    async def run() -> None:
        engine = create_engine(postgres_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            await seed_catalog(session, json.loads(MINI.read_text()))
            await session.commit()
            bench = await session.scalar(
                select(Exercise).where(
                    Exercise.source_id == "Barbell_Bench_Press_-_Medium_Grip"
                )
            )
            assert bench is not None
            result = await retrieve_context(
                session,
                exercise_ids=[str(bench.id)],
                prompt="add 20 lbs to bench press",
            )
        await engine.dispose()
        assert result.exercises
        assert result.exercises[0].source_id == "Barbell_Bench_Press_-_Medium_Grip"

    asyncio.run(run())


def test_retrieve_shoulder_note_for_bench_prompt(postgres_url: str) -> None:
    async def run() -> None:
        engine = create_engine(postgres_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            await seed_catalog(session, json.loads(MINI.read_text()))
            await replace_baseline(
                session, BaselineImport.model_validate(json.loads(SAMPLE.read_text()))
            )
            await session.commit()
            bench = await session.scalar(
                select(Exercise).where(
                    Exercise.source_id == "Barbell_Bench_Press_-_Medium_Grip"
                )
            )
            assert bench is not None
            result = await retrieve_context(
                session,
                exercise_ids=[str(bench.id)],
                prompt="Add 20 lbs to bench tomorrow",
            )
        await engine.dispose()
        quotes = " ".join(note.text for note in result.notes).casefold()
        assert "shoulder felt tight" in quotes
        assert result.notes[0].source_id

    asyncio.run(run())
