from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from overdone.ingest.embed import embed_query, embed_texts
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


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_l = sum(a * a for a in left) ** 0.5
    norm_r = sum(b * b for b in right) ** 0.5
    if norm_l == 0 or norm_r == 0:
        return 0.0
    return dot / (norm_l * norm_r)


async def _embed_name_nearest(session: AsyncSession, name: str) -> str | None:
    rows = list(
        (
            await session.scalars(
                select(Exercise).options(selectinload(Exercise.aliases))
            )
        ).all()
    )
    if not rows:
        return None
    labels: list[tuple[str, str]] = []
    texts: list[str] = []
    for exercise in rows:
        labels.append((str(exercise.id), exercise.name))
        texts.append(exercise.name)
        for alias in exercise.aliases:
            labels.append((str(exercise.id), alias.alias))
            texts.append(alias.alias)
    query = embed_query(name)
    vectors = embed_texts(texts)
    ranked = sorted(
        (
            (_cosine(query, vector), exercise_id)
            for vector, (exercise_id, _label) in zip(vectors, labels, strict=True)
        ),
        reverse=True,
    )
    if not ranked or ranked[0][0] < SIMILARITY_THRESHOLD:
        return None
    return ranked[0][1]


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

    query = embed_query(name)
    similarity = (1 - DataEmbedding.embedding.cosine_distance(query)).label("sim")
    row = (
        await session.execute(
            select(DataEmbedding, similarity)
            .where(DataEmbedding.metadata_["kind"].astext == "exercise")
            .order_by(DataEmbedding.embedding.cosine_distance(query))
            .limit(1)
        )
    ).first()
    if row is not None:
        chunk, score = row
        if float(score) >= SIMILARITY_THRESHOLD:
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
    return await _embed_name_nearest(session, name)


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
