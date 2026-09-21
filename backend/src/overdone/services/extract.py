from __future__ import annotations

import inspect
import logging
import re

from pydantic import ValidationError
from pydantic_ai import AgentRunError

from overdone.schemas.dto import ExtractedPrompt, PromptKind, ProposedItem, Unit
from overdone.services.units import to_kg

logger = logging.getLogger(__name__)

_LLM_FALLBACK = (
    TimeoutError,
    ConnectionError,
    OSError,
    ValidationError,
    AgentRunError,
)

_FATIGUE = re.compile(
    r"(slept\s+\d+\s+hours(?:[^,.]*beat up)?|feel beat up|beat up)",
    re.I,
)
_WEEKS = re.compile(r"in\s+(\d+)\s+weeks", re.I)
_MACRO_REACH = re.compile(
    r"reach\s+(?:a\s+)?(\d+(?:\.\d+)?)\s*(lbs?|kg)\s+(.+?)\s+by\s+next\s+month",
    re.I,
)
_MACRO_WANT = re.compile(
    r"want to\s+(\w+)\s+(\d+(?:\.\d+)?)(?:\s*(lbs?|kg))?\s+by\s+next\s+month",
    re.I,
)
_PLUS_WEIGHT = re.compile(
    r"\+(\d+(?:\.\d+)?)\s*(lbs?|kg)\s+(.+?)(?=,| and |$)",
    re.I,
)
_PLUS_SETS = re.compile(
    r"\+(\d+)\s+sets?\s+(?:of\s+)?(.+?)(?=,| and |$)",
    re.I,
)
_EXTRA_SETS = re.compile(
    r"(\d+)\s+extra\s+sets?\s+(?:of\s+)?(.+?)(?=,| and |$)",
    re.I,
)
_TO_WEIGHT = re.compile(
    r"(\d+(?:\.\d+)?)\s*(lbs?|kg)?\s+to\s+(?:my\s+)?(.+?)(?=,| and |$|\s+tomorrow)",
    re.I,
)
_PRESCRIPTION = re.compile(
    r"(\d+)\s+sets?\s+of\s+(\d+(?:\.\d+)?)\s*(lbs?|kg)\s+(.+)",
    re.I,
)
_SETS_REPS_WEIGHT = re.compile(
    r"(.+?)\s+(\d+)\s+sets?\s+of\s+(\d+)\s+reps?,?\s*"
    r"(?:(?:at|@)\s*)?(\d+(?:\.\d+)?)\s*(lbs?|kg)\s*(?:each)?",
    re.I,
)
_SETS_REPS = re.compile(
    r"(\d+)\s+sets?\s+of\s+(\d+)(?:\s+reps?)?",
    re.I,
)
_SUBSTITUTION = (
    "what should i do instead",
    "tell me what to do instead",
    "or tell me what to do",
)


def _norm_unit(raw: str | None) -> Unit | None:
    if raw is None:
        return None
    lowered = raw.casefold()
    if lowered.startswith("lb"):
        return Unit.lb
    if lowered == "kg":
        return Unit.kg
    return None


def _clean_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name).strip(" .,")
    cleaned = re.sub(
        r"^(?:i want to\s+|want to\s+|make\s+(?:my\s+)?|my\s+)+",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"\s+tomorrow$", "", cleaned, flags=re.I)
    cleaned = re.sub(r",$", "", cleaned).strip(" .,")
    return cleaned


def _apply_sets_reps(items: list[ProposedItem], raw: str) -> list[ProposedItem]:
    if len(items) != 1:
        return items
    item = items[0]
    if item.sets is not None or item.reps is not None or item.extra_sets is not None:
        return items
    match = _SETS_REPS.search(raw)
    if match is None:
        return items
    return [
        item.model_copy(
            update={"sets": int(match.group(1)), "reps": int(match.group(2))}
        )
    ]


def _delta_kg(amount: float, unit: Unit | None) -> float:
    if unit is None:
        return amount
    return to_kg(amount, unit.value)


def extract_heuristic(text: str) -> ExtractedPrompt:
    raw = text.strip()
    lower = raw.casefold()
    asks_substitution = any(phrase in lower for phrase in _SUBSTITUTION)
    fatigue_match = _FATIGUE.search(raw)
    declared_fatigue = fatigue_match.group(1).strip() if fatigue_match else None
    unit_seen: Unit | None = None

    weeks_match = _WEEKS.search(raw)
    weeks = int(weeks_match.group(1)) if weeks_match else None
    if re.search(r"next month", lower):
        weeks = weeks or 4

    macro = _MACRO_REACH.search(raw) or _MACRO_WANT.search(raw)
    if macro and weeks:
        if macro.re is _MACRO_REACH:
            amount = float(macro.group(1))
            unit_seen = _norm_unit(macro.group(2))
            exercise = _clean_name(macro.group(3))
        else:
            exercise = _clean_name(macro.group(1))
            amount = float(macro.group(2))
            unit_seen = _norm_unit(macro.group(3))
        target_kg = to_kg(amount, unit_seen.value) if unit_seen else amount
        return ExtractedPrompt(
            kind=PromptKind.macro_goal,
            items=[],
            weeks=weeks,
            target_weight_kg=target_kg,
            target_exercise_name=exercise,
            declared_fatigue=declared_fatigue,
            asks_substitution=asks_substitution,
            unit=unit_seen,
            raw_text=raw,
        )

    items: list[ProposedItem] = []

    for match in _PLUS_WEIGHT.finditer(raw):
        unit_seen = _norm_unit(match.group(2)) or unit_seen
        items.append(
            ProposedItem(
                exercise_name=_clean_name(match.group(3)),
                delta_kg=_delta_kg(float(match.group(1)), _norm_unit(match.group(2))),
            )
        )

    for match in _PLUS_SETS.finditer(raw):
        items.append(
            ProposedItem(
                exercise_name=_clean_name(match.group(2)),
                extra_sets=int(match.group(1)),
            )
        )

    for match in _EXTRA_SETS.finditer(raw):
        items.append(
            ProposedItem(
                exercise_name=_clean_name(match.group(2)),
                extra_sets=int(match.group(1)),
            )
        )

    if not items:
        for match in _TO_WEIGHT.finditer(raw):
            unit_seen = _norm_unit(match.group(2)) or unit_seen
            items.append(
                ProposedItem(
                    exercise_name=_clean_name(match.group(3)),
                    delta_kg=_delta_kg(
                        float(match.group(1)), _norm_unit(match.group(2))
                    ),
                )
            )

    if not items:
        for match in _SETS_REPS_WEIGHT.finditer(raw):
            unit_seen = _norm_unit(match.group(5)) or unit_seen
            amount = float(match.group(4))
            items.append(
                ProposedItem(
                    exercise_name=_clean_name(match.group(1)),
                    weight_kg=(to_kg(amount, unit_seen.value) if unit_seen else amount),
                    sets=int(match.group(2)),
                    reps=int(match.group(3)),
                )
            )

    if not items:
        for match in _PRESCRIPTION.finditer(raw):
            unit_seen = _norm_unit(match.group(3)) or unit_seen
            amount = float(match.group(2))
            items.append(
                ProposedItem(
                    exercise_name=_clean_name(match.group(4)),
                    weight_kg=(to_kg(amount, unit_seen.value) if unit_seen else amount),
                    sets=int(match.group(1)),
                )
            )

    items = _apply_sets_reps(items, raw)

    return ExtractedPrompt(
        kind=PromptKind.single_session,
        items=items,
        weeks=weeks,
        declared_fatigue=declared_fatigue,
        asks_substitution=asks_substitution,
        unit=unit_seen,
        raw_text=raw,
    )


async def extract_prompt(
    text: str, *, llm_client: object | None = None
) -> ExtractedPrompt:
    if llm_client is not None:
        extract = getattr(llm_client, "extract", None)
        if callable(extract):
            try:
                result = extract(text)
                if inspect.isawaitable(result):
                    result = await result
                if isinstance(result, ExtractedPrompt):
                    cleaned = _without_catalog_ids(result)
                    if cleaned.items or cleaned.kind is PromptKind.macro_goal:
                        return cleaned
            except _LLM_FALLBACK:
                logger.warning(
                    "llm extract failed; falling back to heuristic",
                    exc_info=True,
                )
    return extract_heuristic(text)


def _without_catalog_ids(extracted: ExtractedPrompt) -> ExtractedPrompt:
    items = [item.model_copy(update={"exercise_id": None}) for item in extracted.items]
    return extracted.model_copy(update={"items": items})
