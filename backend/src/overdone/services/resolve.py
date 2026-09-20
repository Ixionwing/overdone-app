from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from overdone.ingest.embed import embed_query
from overdone.models.embeddings import DataEmbedding
from overdone.models.exercise import Exercise, ExerciseAlias

SIMILARITY_THRESHOLD = 0.78

_BUILTIN_ALIASES = {
    "db bench": "bench",
    "db bench press": "bench",
    "bench press": "bench",
    "bench": "bench",
    "incline db press": "incline",
    "incline dumbbell press": "incline",
    "pushdowns": "pushdown",
    "pushdown": "pushdown",
    "squat": "squat",
    "ohp": "overhead press",
    "overhead press": "overhead press",
}


def resolve_from_baseline(name: str, baseline_names: list[str]) -> str | None:
    needle = name.casefold().strip()
    for candidate in baseline_names:
        if candidate.casefold() == needle:
            return candidate
    key = _BUILTIN_ALIASES.get(needle, needle)
    if len(key) < 4:
        return None
    for candidate in baseline_names:
        if key in candidate.casefold():
            return candidate
    return None


async def _nearest_kind(session: AsyncSession, name: str, kind: str) -> str | None:
    query = embed_query(name)
    similarity = (1 - DataEmbedding.embedding.cosine_distance(query)).label("sim")
    row = (
        await session.execute(
            select(DataEmbedding, similarity)
            .where(DataEmbedding.metadata_["kind"].astext == kind)
            .order_by(DataEmbedding.embedding.cosine_distance(query))
            .limit(1)
        )
    ).first()
    if row is None:
        return None
    chunk, score = row
    if float(score) < SIMILARITY_THRESHOLD:
        return None
    meta = chunk.metadata_ or {}
    if meta.get("exercise_id"):
        return str(meta["exercise_id"])
    source_id = meta.get("source_id")
    if source_id:
        matched = await session.scalar(
            select(Exercise).where(Exercise.source_id == source_id)
        )
        if matched is not None:
            return str(matched.id)
    return None


async def resolve_exercise_name(session: AsyncSession, name: str) -> str | None:
    needle = name.casefold().strip()
    if not needle:
        return None
    alias = await session.scalar(
        select(ExerciseAlias).where(func.lower(ExerciseAlias.alias) == needle)
    )
    if alias is not None:
        return str(alias.exercise_id)
    exact = await session.scalar(
        select(Exercise).where(func.lower(Exercise.name) == needle)
    )
    if exact is not None:
        return str(exact.id)
    return await _nearest_kind(session, name, "exercise") or await _nearest_kind(
        session, name, "exercise_name"
    )


async def history_name_for_catalog(
    session: AsyncSession, catalog_id: str, baseline_names: list[str]
) -> str | None:
    exercise = await session.scalar(
        select(Exercise)
        .options(selectinload(Exercise.aliases))
        .where(Exercise.id == int(catalog_id))
    )
    if exercise is None:
        return None
    candidates = [exercise.name, *[item.alias for item in exercise.aliases]]
    for candidate in candidates:
        resolved = resolve_from_baseline(candidate, baseline_names)
        if resolved:
            return resolved
        for baseline in baseline_names:
            if baseline.casefold() == candidate.casefold():
                return baseline
    return None
