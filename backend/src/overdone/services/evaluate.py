from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from overdone.schemas.dto import (
    EvaluationResult,
    ExerciseEnrichment,
    ExtractedPrompt,
    Halt,
    HaltReason,
    ItemVerdict,
    LogSet,
    PromptKind,
    ProposedItem,
    Unit,
    WarningFlag,
)
from overdone.services.bind import bind_name, load_enrichment, with_citation
from overdone.services.extract import extract_prompt
from overdone.services.history import (
    baseline_names,
    inherit_unit,
    last_working,
    load_history,
    stored_units,
    weekly_velocity,
)
from overdone.services.narrative import (
    macro_narrative,
    scope_disclaimer,
    session_narrative,
)
from overdone.services.retrieve import note_banner, retrieve_context
from overdone.services.scoring import score_macro, score_session

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


async def _retrieve_support(
    session: AsyncSession, prompt: str, exercise_ids: list[str]
) -> tuple[list[WarningFlag], dict[str, str]]:
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
    citations = {
        chunk.exercise_id: chunk.source_id
        for chunk in retrieved.exercises
        if chunk.exercise_id and chunk.source_id
    }
    return flags, citations


async def evaluate_prompt(
    session: AsyncSession, prompt: str, *, llm_client: object | None = None
) -> EvaluationResult:
    extracted = await extract_prompt(prompt, llm_client=llm_client)
    sessions, benchmarks, preferred = await load_history(session)
    if not sessions and not benchmarks:
        return _halt(HaltReason.missing_baseline, _MISSING_BASELINE)

    stored = stored_units(sessions, benchmarks)
    if extracted.unit is None and len(stored) > 1:
        return _halt(HaltReason.ambiguous_units, _AMBIGUOUS_UNITS)

    inherit = Unit(next(iter(stored)) if len(stored) == 1 else preferred)
    extracted = inherit_unit(extracted, inherit)
    names = baseline_names(sessions, benchmarks)
    flags = _warnings(extracted)

    if extracted.kind is PromptKind.macro_goal:
        raw_name = extracted.target_exercise_name or ""
        history, catalog_id = await bind_name(session, raw_name, names)
        if history is None:
            return _halt(
                HaltReason.missing_exercise,
                _MISSING_EXERCISE.format(name=raw_name or "that exercise"),
                exercise_name=raw_name or None,
            )
        last = last_working({history, raw_name}, sessions, benchmarks)
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
        enrich = await load_enrichment(session, catalog_id)
        verdict = score_macro(
            current_kg=last.weight_kg,
            target_kg=target,
            weeks=weeks,
            weekly_velocity_kg=weekly_velocity({history, raw_name}, sessions),
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
        extra, citations = await _retrieve_support(
            session, prompt, [catalog_id or history]
        )
        flags.extend(extra)
        verdict = await with_citation(session, verdict, citations, catalog_id)
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
        history, catalog_id = await bind_name(session, item.exercise_name, names)
        if history is None:
            return _halt(
                HaltReason.missing_exercise,
                _MISSING_EXERCISE.format(name=item.exercise_name),
                exercise_name=item.exercise_name,
            )
        last = last_working({history, item.exercise_name}, sessions, benchmarks)
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
        enrichment[key] = await load_enrichment(session, catalog_id)
        catalog_ids.append(key)

    overall, verdicts, factors = score_session(resolved_items, last_by, enrichment)
    extra, citations = await _retrieve_support(session, prompt, catalog_ids)
    flags.extend(extra)
    cited: list[ItemVerdict] = []
    for verdict, item in zip(verdicts, resolved_items, strict=True):
        cited.append(await with_citation(session, verdict, citations, item.exercise_id))
    return EvaluationResult(
        overall_light=overall,
        items=cited,
        session_factors=factors,
        narrative=session_narrative(overall, cited, factors),
        warnings=flags,
    )
