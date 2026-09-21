from __future__ import annotations

from collections.abc import Sequence
from typing import Any

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
from overdone.services.baseline import parse_baseline_text
from overdone.services.bind import bind_name, load_enrichment, with_citation
from overdone.services.extract import ExtractError, extract_prompt
from overdone.services.history import (
    baseline_names,
    history_from_import,
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
from overdone.services.retrieve import (
    is_qualitative_note,
    note_banner,
    retrieve_context,
)
from overdone.services.scoring import score_macro, score_session

_MISSING_BASELINE = "Import a training baseline before evaluating a prompt."
_MISSING_EXERCISE = (
    "No history for {name}. Enter a 1RM or working weight before rendering a verdict."
)
_AMBIGUOUS_UNITS = "Say whether the load is lb or kg before rendering a verdict."
_EXTRACT_FAILED = "Could not extract a proposed change from the prompt."


def resolve_macro_target_kg(
    extracted: ExtractedPrompt, last_weight_kg: float
) -> float | None:
    if extracted.target_weight_kg is not None:
        return extracted.target_weight_kg
    for item in extracted.items:
        if item.delta_kg is not None:
            return last_weight_kg + item.delta_kg
    return None


def macro_sets_reps(extracted: ExtractedPrompt, last: LogSet) -> tuple[int, int]:
    item = extracted.items[0] if extracted.items else None
    sets = last.sets
    reps = last.reps
    if item is not None:
        if item.sets is not None:
            sets = item.sets
        if item.reps is not None:
            reps = item.reps
    return sets, reps


def _halt(
    reason: HaltReason, message: str, exercise_name: str | None = None
) -> EvaluationResult:
    return EvaluationResult(
        halted=Halt(reason=reason, message=message, exercise_name=exercise_name)
    )


def _inline_note_flags(sessions: Sequence[Any]) -> list[WarningFlag]:
    flags: list[WarningFlag] = []
    for logged in sessions:
        text = (logged.notes or "").strip()
        if not text or not is_qualitative_note(text):
            continue
        flags.append(
            WarningFlag(
                kind="qualitative_note",
                message=note_banner(logged.logged_on, text),
                source_id=None,
            )
        )
    return flags


def _with_extract(
    result: EvaluationResult,
    extracted: ExtractedPrompt,
    *,
    extra_warnings: list[WarningFlag] | None = None,
) -> EvaluationResult:
    warnings = list(result.warnings)
    if extra_warnings:
        warnings.extend(extra_warnings)
    return result.model_copy(
        update={
            "warnings": warnings,
            "extract": extracted.model_dump(mode="json"),
        }
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
    session: AsyncSession,
    prompt: str,
    *,
    llm_client: object | None = None,
    log_text: str | None = None,
) -> EvaluationResult:
    inline = bool(log_text and log_text.strip())
    if inline:
        sessions, benchmarks, preferred = history_from_import(
            parse_baseline_text(log_text or "")
        )
        note_flags = _inline_note_flags(sessions)
    else:
        sessions, benchmarks, preferred = await load_history(session)
        note_flags = []
    if not sessions and not benchmarks:
        return _halt(HaltReason.missing_baseline, _MISSING_BASELINE)

    try:
        extracted = await extract_prompt(prompt, llm_client=llm_client)
    except ExtractError:
        return _halt(HaltReason.extract_failed, _EXTRACT_FAILED)

    def finish(result: EvaluationResult) -> EvaluationResult:
        return _with_extract(result, extracted, extra_warnings=note_flags)

    stored = stored_units(sessions, benchmarks)
    if extracted.unit is None and len(stored) > 1:
        return finish(_halt(HaltReason.ambiguous_units, _AMBIGUOUS_UNITS))

    inherit = Unit(next(iter(stored)) if len(stored) == 1 else preferred)
    extracted = inherit_unit(extracted, inherit)
    names = baseline_names(sessions, benchmarks)
    flags = _warnings(extracted)

    if extracted.kind is PromptKind.macro_goal:
        raw_name = extracted.target_exercise_name or ""
        history, catalog_id = await bind_name(session, raw_name, names)
        if history is None:
            return finish(
                _halt(
                    HaltReason.missing_exercise,
                    _MISSING_EXERCISE.format(name=raw_name or "that exercise"),
                    exercise_name=raw_name or None,
                )
            )
        last = last_working({history, raw_name}, sessions, benchmarks)
        if last is None:
            return finish(
                _halt(
                    HaltReason.missing_exercise,
                    _MISSING_EXERCISE.format(name=history),
                    exercise_name=history,
                )
            )
        weeks = extracted.weeks or 4
        target = resolve_macro_target_kg(extracted, last.weight_kg)
        if target is None:
            return finish(
                _halt(
                    HaltReason.missing_exercise,
                    "Macro goal is missing a target weight.",
                    exercise_name=history,
                )
            )
        sets, reps = macro_sets_reps(extracted, last)
        enrich = await load_enrichment(session, catalog_id)
        verdict = score_macro(
            current_kg=last.weight_kg,
            target_kg=target,
            weeks=weeks,
            weekly_velocity_kg=weekly_velocity({history, raw_name}, sessions),
            working=last,
            enrichment=enrich,
            target_sets=sets,
            target_reps=reps,
        )
        verdict = verdict.model_copy(
            update={
                "exercise_id": catalog_id or history,
                "exercise_name": last.exercise_name,
                "narrative": macro_narrative(verdict, weeks, sets=sets, reps=reps),
            }
        )
        extra, citations = await _retrieve_support(
            session, prompt, [catalog_id or history]
        )
        flags.extend(extra)
        verdict = await with_citation(session, verdict, citations, catalog_id)
        return finish(
            EvaluationResult(
                overall_light=verdict.light,
                items=[verdict],
                session_factors=verdict.factors,
                narrative=macro_narrative(verdict, weeks, sets=sets, reps=reps),
                warnings=flags,
            )
        )

    resolved_items: list[ProposedItem] = []
    last_by: dict[str, LogSet] = {}
    enrichment: dict[str, ExerciseEnrichment] = {}
    catalog_ids: list[str] = []
    for item in extracted.items:
        history, catalog_id = await bind_name(session, item.exercise_name, names)
        if history is None:
            return finish(
                _halt(
                    HaltReason.missing_exercise,
                    _MISSING_EXERCISE.format(name=item.exercise_name),
                    exercise_name=item.exercise_name,
                )
            )
        last = last_working({history, item.exercise_name}, sessions, benchmarks)
        if last is None:
            return finish(
                _halt(
                    HaltReason.missing_exercise,
                    _MISSING_EXERCISE.format(name=history),
                    exercise_name=history,
                )
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
    return finish(
        EvaluationResult(
            overall_light=overall,
            items=cited,
            session_factors=factors,
            narrative=session_narrative(overall, cited, factors),
            warnings=flags,
        )
    )
