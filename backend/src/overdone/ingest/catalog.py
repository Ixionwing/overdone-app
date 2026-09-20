from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from overdone.ingest.embed import embed_texts
from overdone.ingest.enrichment import as_list, chunk_text, enrichment_for, load_rules
from overdone.ingest.vectorstore import OverdoneVectorStore, exercise_node, name_node
from overdone.models.exercise import Exercise, ExerciseAlias, ExerciseEnrichment


async def seed_catalog(session: AsyncSession, exercises: list[dict[str, Any]]) -> int:
    rules = load_rules()
    store = OverdoneVectorStore(session=session)
    chunk_texts = [chunk_text(item, enrichment_for(item, rules)) for item in exercises]
    name_specs: list[tuple[str, str, str]] = []
    for item in exercises:
        source_id = str(item.get("id") or item.get("source_id") or "")
        name = str(item.get("name") or "")
        name_specs.append((source_id, name, "name"))
        for alias in (rules.get("aliases") or {}).get(source_id, []):
            name_specs.append((source_id, str(alias), f"alias:{alias}"))
    embeddings = (
        await embed_texts([*chunk_texts, *[spec[1] for spec in name_specs]])
        if chunk_texts or name_specs
        else []
    )
    chunk_vectors = embeddings[: len(chunk_texts)]
    name_vectors = embeddings[len(chunk_texts) :]

    for item, text, embedding in zip(
        exercises, chunk_texts, chunk_vectors, strict=True
    ):
        source_id = str(item.get("id") or item.get("source_id") or "")
        if not source_id:
            raise ValueError("exercise is missing id")
        name = str(item["name"])
        existing = await session.scalar(
            select(Exercise).where(Exercise.source_id == source_id)
        )
        if existing is None:
            existing = Exercise(source_id=source_id, name=name)
            session.add(existing)
            await session.flush()
        existing.name = name
        existing.force = item.get("force")
        existing.level = item.get("level")
        existing.mechanic = item.get("mechanic")
        existing.equipment = item.get("equipment")
        existing.category = item.get("category")
        existing.primary_muscles = as_list(
            item.get("primaryMuscles") or item.get("primary_muscles")
        )
        existing.secondary_muscles = as_list(
            item.get("secondaryMuscles") or item.get("secondary_muscles")
        )
        existing.instructions = as_list(item.get("instructions"))
        await session.flush()

        factors = enrichment_for(item, rules)
        enrich = await session.get(ExerciseEnrichment, existing.id)
        if enrich is None:
            enrich = ExerciseEnrichment(exercise_id=existing.id, **factors)
            session.add(enrich)
        else:
            enrich.axial_factor = factors["axial_factor"]
            enrich.cns_factor = factors["cns_factor"]
            enrich.joints = factors["joints"]

        aliases = (rules.get("aliases") or {}).get(source_id, [])
        for alias in aliases:
            found = await session.scalar(
                select(ExerciseAlias).where(ExerciseAlias.alias == alias)
            )
            if found is None:
                session.add(ExerciseAlias(exercise_id=existing.id, alias=alias))

        await store.adelete(source_id)
        name_nodes = [
            name_node(
                source_id=source_id,
                exercise_id=str(existing.id),
                text=label_text,
                embedding=vector,
                label=label,
            )
            for (spec_source, label_text, label), vector in zip(
                name_specs, name_vectors, strict=True
            )
            if spec_source == source_id
        ]
        await store.async_add(
            [
                exercise_node(
                    source_id=source_id,
                    exercise_id=str(existing.id),
                    text=text,
                    embedding=embedding,
                ),
                *name_nodes,
            ]
        )

    await session.flush()
    return len(exercises)
