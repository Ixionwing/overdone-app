from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from overdone.config import settings
from overdone.ingest.embed import embed_texts
from overdone.ingest.vectorstore import OverdoneVectorStore, exercise_node, name_node
from overdone.models.exercise import Exercise, ExerciseAlias, ExerciseEnrichment

_JOINTS = ("shoulder", "knee", "spine", "elbow")
_PRESS_MUSCLES = {"chest", "shoulders", "triceps"}
_KNEE_MUSCLES = {"quadriceps", "quads", "glutes", "gluteus maximus"}
_AXIAL_IDS = ("squat", "deadlift", "good-morning", "good_morning")


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _load_rules() -> dict[str, Any]:
    path = settings.resolved_enrichment_rules_path()
    if not path.exists():
        return {"aliases": {}, "by_source_id": {}, "defaults": {}}
    return json.loads(path.read_text())


def enrichment_for(exercise: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    source_id = str(exercise.get("id") or exercise.get("source_id") or "")
    name = str(exercise.get("name") or "").casefold()
    mechanic = str(exercise.get("mechanic") or "").casefold()
    category = str(exercise.get("category") or "").casefold()
    primary = [
        m.casefold()
        for m in _as_list(
            exercise.get("primaryMuscles") or exercise.get("primary_muscles")
        )
    ]
    secondary = [
        m.casefold()
        for m in _as_list(
            exercise.get("secondaryMuscles") or exercise.get("secondary_muscles")
        )
    ]
    muscles = set(primary + secondary)
    defaults = rules.get("defaults") or {}
    overlay = (rules.get("by_source_id") or {}).get(source_id, {})

    axial = float(overlay.get("axial_factor", defaults.get("axial_factor", 0.15)))
    if any(token in source_id.casefold() or token in name for token in _AXIAL_IDS):
        axial = float(overlay.get("axial_factor", 0.9))
    elif "lower back" in muscles or "hinge" in mechanic:
        axial = float(overlay.get("axial_factor", 0.6))

    if mechanic == "compound":
        cns = 0.85
    elif category in {"olympic weightlifting", "strongman", "olympic"}:
        cns = 0.5
    else:
        cns = 0.25
    cns = float(overlay.get("cns_factor", cns))

    joints = {
        "shoulder": 0.0,
        "knee": 0.0,
        "spine": axial,
        "elbow": 0.0,
    }
    if muscles & _PRESS_MUSCLES or "press" in name:
        joints["shoulder"] = (
            0.7 if "chest" in primary or "shoulders" in primary else 0.4
        )
        joints["elbow"] = 0.35
    if muscles & _KNEE_MUSCLES or "squat" in name or "lunge" in name:
        joints["knee"] = 0.7
    for key in _JOINTS:
        if key in overlay.get("joints", {}):
            joints[key] = float(overlay["joints"][key])
    return {"axial_factor": axial, "cns_factor": cns, "joints": joints}


def _chunk_text(exercise: dict[str, Any], factors: dict[str, Any]) -> str:
    name = exercise.get("name") or ""
    muscles = ", ".join(
        _as_list(exercise.get("primaryMuscles") or exercise.get("primary_muscles"))
    )
    instructions = " ".join(_as_list(exercise.get("instructions")))
    blurb = (
        f"axial_factor={factors['axial_factor']} "
        f"cns_factor={factors['cns_factor']} joints={factors['joints']}"
    )
    return f"{name}. Muscles: {muscles}. {instructions} {blurb}".strip()


async def seed_catalog(session: AsyncSession, exercises: list[dict[str, Any]]) -> int:
    rules = _load_rules()
    store = OverdoneVectorStore(session=session)
    chunk_texts = [_chunk_text(item, enrichment_for(item, rules)) for item in exercises]
    name_specs: list[tuple[str, str, str]] = []
    for item in exercises:
        source_id = str(item.get("id") or item.get("source_id") or "")
        name = str(item.get("name") or "")
        name_specs.append((source_id, name, "name"))
        for alias in (rules.get("aliases") or {}).get(source_id, []):
            name_specs.append((source_id, str(alias), f"alias:{alias}"))
    embeddings = (
        embed_texts([*chunk_texts, *[spec[1] for spec in name_specs]])
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
        existing.primary_muscles = _as_list(
            item.get("primaryMuscles") or item.get("primary_muscles")
        )
        existing.secondary_muscles = _as_list(
            item.get("secondaryMuscles") or item.get("secondary_muscles")
        )
        existing.instructions = _as_list(item.get("instructions"))
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
