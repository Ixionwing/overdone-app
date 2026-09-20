from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from overdone.models.exercise import Exercise
from overdone.models.exercise import ExerciseEnrichment as EnrichmentRow
from overdone.schemas.dto import DEFAULT_ENRICHMENT, ExerciseEnrichment, ItemVerdict
from overdone.services.resolve import (
    history_name_for_catalog,
    resolve_exercise_name,
    resolve_from_baseline,
)


async def load_enrichment(
    session: AsyncSession, catalog_id: str | None
) -> ExerciseEnrichment:
    if not catalog_id:
        return DEFAULT_ENRICHMENT
    row = await session.get(EnrichmentRow, int(catalog_id))
    if row is None:
        return DEFAULT_ENRICHMENT
    return ExerciseEnrichment(
        axial_factor=row.axial_factor,
        cns_factor=row.cns_factor,
        joints=dict(row.joints or {}),
    )


async def bind_name(
    session: AsyncSession, raw_name: str, baseline_names: list[str]
) -> tuple[str | None, str | None]:
    stub = resolve_from_baseline(raw_name, baseline_names)
    catalog_id = await resolve_exercise_name(session, raw_name)
    if catalog_id is None and stub:
        catalog_id = await resolve_exercise_name(session, stub)
    history = stub
    if history is None and catalog_id:
        history = await history_name_for_catalog(session, catalog_id, baseline_names)
    return history, catalog_id


async def catalog_source_id(
    session: AsyncSession, catalog_id: str | None
) -> str | None:
    if not catalog_id or not catalog_id.isdigit():
        return None
    row = await session.get(Exercise, int(catalog_id))
    return row.source_id if row else None


async def with_citation(
    session: AsyncSession,
    verdict: ItemVerdict,
    citations: dict[str, str],
    catalog_id: str | None,
) -> ItemVerdict:
    source = citations.get(verdict.exercise_id)
    if source is None:
        source = await catalog_source_id(session, catalog_id)
    return verdict.model_copy(update={"catalog_source_id": source})
