from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from overdone.models.exercise import ExerciseEnrichment as EnrichmentRow
from overdone.models.user_log import UserBenchmark, UserSession, UserSettings
from overdone.schemas.dto import (
    DEFAULT_ENRICHMENT,
    EvaluationResult,
    ExerciseEnrichment,
    ExtractedPrompt,
    Halt,
    HaltReason,
    LogSet,
    PromptKind,
    ProposedItem,
    Unit,
    WarningFlag,
)
from overdone.services.extract import extract_prompt
from overdone.services.narrative import (
    macro_narrative,
    scope_disclaimer,
    session_narrative,
)
from overdone.services.resolve import (
    history_name_for_catalog,
    resolve_exercise_name,
    resolve_from_baseline,
)
from overdone.services.retrieve import note_banner, retrieve_context
from overdone.services.scoring import score_macro, score_session
from overdone.services.units import to_kg

_MISSING_BASELINE = "Import a training baseline before evaluating a prompt."
_MISSING_EXERCISE = (
    "No history for {name}. Enter a 1RM or working weight before rendering a verdict."
)
_AMBIGUOUS_UNITS = "Say whether the load is lb or kg before rendering a verdict."


def _halt(
    reason: HaltReason, message: str, exercise_name: str | None = None
) -> EvaluationResult:
    return EvaluationResult(
        halted=Halt(reason=reason, message=message, exercise_name=exercise_name)
    )


async def _history(
    session: AsyncSession,
) -> tuple[list[UserSession], list[UserBenchmark], str]:
    settings = await session.get(UserSettings, 1)
    preferred = settings.preferred_unit if settings else "lb"
    sessions = list(
        (
            await session.scalars(
                select(UserSession)
                .options(selectinload(UserSession.sets))
                .order_by(UserSession.logged_on.desc(), UserSession.id.desc())
            )
        ).all()
    )
    benchmarks = list(
        (await session.scalars(select(UserBenchmark).order_by(UserBenchmark.id))).all()
    )
    return sessions, benchmarks, preferred


def _stored_units(
    sessions: list[UserSession], benchmarks: list[UserBenchmark]
) -> set[str]:
    units = {row.unit for row in benchmarks}
    for logged in sessions:
        for item in logged.sets:
            units.add(item.unit)
    return units


def _baseline_names(
    sessions: list[UserSession], benchmarks: list[UserBenchmark]
) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for logged in sessions:
        for item in logged.sets:
            if item.exercise_name not in seen:
                names.append(item.exercise_name)
                seen.add(item.exercise_name)
    for row in benchmarks:
        if row.exercise_name not in seen:
            names.append(row.exercise_name)
            seen.add(row.exercise_name)
    return names


def _inherit_unit(extracted: ExtractedPrompt, unit: Unit) -> ExtractedPrompt:
    if extracted.unit is not None:
        return extracted
    items: list[ProposedItem] = []
    for item in extracted.items:
        delta = to_kg(item.delta_kg, unit.value) if item.delta_kg is not None else None
        weight = (
            to_kg(item.weight_kg, unit.value) if item.weight_kg is not None else None
        )
        items.append(item.model_copy(update={"delta_kg": delta, "weight_kg": weight}))
    target = (
        to_kg(extracted.target_weight_kg, unit.value)
        if extracted.target_weight_kg is not None
        else None
    )
    return extracted.model_copy(
        update={"items": items, "target_weight_kg": target, "unit": unit}
    )


def _last_working(
    names: set[str], sessions: list[UserSession], benchmarks: list[UserBenchmark]
) -> LogSet | None:
    folded = {name.casefold() for name in names if name}
    for logged in sessions:
        matching = [
            row for row in logged.sets if row.exercise_name.casefold() in folded
        ]
        if matching:
            heaviest = max(matching, key=lambda row: row.weight_kg)
            return LogSet(
                exercise_id=heaviest.exercise_name,
                exercise_name=heaviest.exercise_name,
                weight_kg=heaviest.weight_kg,
                reps=heaviest.reps,
                sets=heaviest.sets,
            )
    for row in benchmarks:
        if row.exercise_name.casefold() in folded:
            return LogSet(
                exercise_id=row.exercise_name,
                exercise_name=row.exercise_name,
                weight_kg=0.80 * row.one_rm_kg,
                reps=5,
                sets=3,
            )
    return None


def _weekly_velocity(names: set[str], sessions: list[UserSession]) -> float:
    folded = {name.casefold() for name in names if name}
    points: list[tuple[date, float]] = []
    chronological = list(reversed(sessions))
    for logged in chronological:
        matching = [
            row for row in logged.sets if row.exercise_name.casefold() in folded
        ]
        if matching:
            points.append((logged.logged_on, max(row.weight_kg for row in matching)))
    points = points[-8:]
    if len(points) < 2:
        return 0.0
    days = (points[-1][0] - points[0][0]).days
    if days <= 0:
        return 0.0
    return (points[-1][1] - points[0][1]) / (days / 7.0)


def _warnings(extracted: ExtractedPrompt) -> list[WarningFlag]:
    flags: list[WarningFlag] = []
    if extracted.declared_fatigue:
        flags.append(
            WarningFlag(
                kind="in_prompt_fatigue",
                message=f"User declared: '{extracted.declared_fatigue}'",
                source_id=None,
            )
        )
    if extracted.asks_substitution:
        flags.append(scope_disclaimer())
    return flags


async def _enrichment_for(
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


async def _bind_name(
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


async def _note_flags(
    session: AsyncSession, prompt: str, exercise_ids: list[str]
) -> list[WarningFlag]:
    retrieved = await retrieve_context(
        session, exercise_ids=exercise_ids, prompt=prompt
    )
    flags: list[WarningFlag] = []
    for note in retrieved.notes:
        if note.logged_on is None:
            continue
        flags.append(
            WarningFlag(
                kind="qualitative_note",
                message=note_banner(note.logged_on, note.text),
                source_id=note.source_id,
            )
        )
    return flags


async def evaluate_prompt(session: AsyncSession, prompt: str) -> EvaluationResult:
    extracted = await extract_prompt(prompt, llm_client=None)
    sessions, benchmarks, preferred = await _history(session)
    if not sessions and not benchmarks:
        return _halt(HaltReason.missing_baseline, _MISSING_BASELINE)

    stored = _stored_units(sessions, benchmarks)
    if extracted.unit is None and len(stored) > 1:
        return _halt(HaltReason.ambiguous_units, _AMBIGUOUS_UNITS)

    inherit = Unit(next(iter(stored)) if len(stored) == 1 else preferred)
    extracted = _inherit_unit(extracted, inherit)
    names = _baseline_names(sessions, benchmarks)
    flags = _warnings(extracted)

    if extracted.kind is PromptKind.macro_goal:
        raw_name = extracted.target_exercise_name or ""
        history, catalog_id = await _bind_name(session, raw_name, names)
        if history is None:
            return _halt(
                HaltReason.missing_exercise,
                _MISSING_EXERCISE.format(name=raw_name or "that exercise"),
                exercise_name=raw_name or None,
            )
        last = _last_working({history, raw_name}, sessions, benchmarks)
        if last is None:
            return _halt(
                HaltReason.missing_exercise,
                _MISSING_EXERCISE.format(name=history),
                exercise_name=history,
            )
        weeks = extracted.weeks or 4
        target = extracted.target_weight_kg
        if target is None:
            return _halt(
                HaltReason.missing_exercise,
                "Macro goal is missing a target weight.",
                exercise_name=history,
            )
        enrich = await _enrichment_for(session, catalog_id)
        verdict = score_macro(
            current_kg=last.weight_kg,
            target_kg=target,
            weeks=weeks,
            weekly_velocity_kg=_weekly_velocity({history, raw_name}, sessions),
            working=last,
            enrichment=enrich,
        )
        verdict = verdict.model_copy(
            update={
                "exercise_id": catalog_id or history,
                "exercise_name": last.exercise_name,
                "narrative": macro_narrative(verdict, weeks),
            }
        )
        flags.extend(await _note_flags(session, prompt, [catalog_id or history]))
        return EvaluationResult(
            overall_light=verdict.light,
            items=[verdict],
            session_factors=verdict.factors,
            narrative=macro_narrative(verdict, weeks),
            warnings=flags,
        )

    if not extracted.items:
        return _halt(
            HaltReason.missing_exercise,
            "Could not extract a proposed change from the prompt.",
        )

    resolved_items: list[ProposedItem] = []
    last_by: dict[str, LogSet] = {}
    enrichment: dict[str, ExerciseEnrichment] = {}
    catalog_ids: list[str] = []
    for item in extracted.items:
        history, catalog_id = await _bind_name(session, item.exercise_name, names)
        if history is None:
            return _halt(
                HaltReason.missing_exercise,
                _MISSING_EXERCISE.format(name=item.exercise_name),
                exercise_name=item.exercise_name,
            )
        last = _last_working({history, item.exercise_name}, sessions, benchmarks)
        if last is None:
            return _halt(
                HaltReason.missing_exercise,
                _MISSING_EXERCISE.format(name=history),
                exercise_name=history,
            )
        key = catalog_id or history
        bound = item.model_copy(
            update={"exercise_id": key, "exercise_name": last.exercise_name}
        )
        last = last.model_copy(update={"exercise_id": key})
        resolved_items.append(bound)
        last_by[key] = last
        enrichment[key] = await _enrichment_for(session, catalog_id)
        catalog_ids.append(key)

    overall, verdicts, factors = score_session(resolved_items, last_by, enrichment)
    flags.extend(await _note_flags(session, prompt, catalog_ids))
    return EvaluationResult(
        overall_light=overall,
        items=verdicts,
        session_factors=factors,
        narrative=session_narrative(overall, verdicts, factors),
        warnings=flags,
    )
