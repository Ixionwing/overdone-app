from __future__ import annotations

import re

from overdone.schemas.dto import ExtractedPrompt, PromptKind, ProposedItem, Unit
from overdone.schemas.extract_draft import AmountKind, DraftItem, ExtractDraft
from overdone.services.units import to_kg

_WEEKS = re.compile(r"\b(\d+)\s*weeks?\b", re.I)
_MONTHS = re.compile(r"\b(\d+)\s*months?\b", re.I)
_THIRTY_DAYS = re.compile(r"\b30\s*days\b", re.I)
_A_MONTH = re.compile(r"\b(?:a|next|this)\s+month\b|\bin a month\b", re.I)


def weeks_from_raw(raw: str) -> int | None:
    match = _WEEKS.search(raw)
    if match:
        return int(match.group(1))
    match = _MONTHS.search(raw)
    if match:
        return int(match.group(1)) * 4
    if _THIRTY_DAYS.search(raw):
        return 4
    if _A_MONTH.search(raw):
        return 4
    return None


def _amount_kg(item: DraftItem) -> float | None:
    if item.amount is None:
        return None
    if item.amount_unit is None:
        return item.amount
    return to_kg(item.amount, item.amount_unit)


def _map_item(item: DraftItem) -> ProposedItem:
    amount = _amount_kg(item)
    if item.amount_kind is AmountKind.extra_sets:
        extra = int(item.amount) if item.amount is not None else None
        return ProposedItem(
            exercise_name=item.name,
            extra_sets=extra,
            sets=item.sets,
            reps=item.reps,
        )
    if item.amount_kind is AmountKind.delta:
        return ProposedItem(
            exercise_name=item.name,
            delta_kg=amount,
            sets=item.sets,
            reps=item.reps,
        )
    if item.amount_kind is AmountKind.absolute:
        return ProposedItem(
            exercise_name=item.name,
            weight_kg=amount,
            sets=item.sets,
            reps=item.reps,
        )
    return ProposedItem(
        exercise_name=item.name,
        sets=item.sets,
        reps=item.reps,
    )


def _prompt_unit(draft: ExtractDraft) -> Unit | None:
    named = [item.amount_unit for item in draft.items if item.amount_unit]
    if not named:
        return None
    unique = set(named)
    if unique == {"lb"}:
        return Unit.lb
    if unique == {"kg"}:
        return Unit.kg
    return Unit.kg


def to_extracted_prompt(draft: ExtractDraft, raw: str) -> ExtractedPrompt:
    items = [_map_item(item) for item in draft.items]
    first = items[0] if items else None
    weeks = draft.weeks if draft.weeks else weeks_from_raw(raw)
    target_weight = None
    target_name = None
    if draft.kind == "macro_goal" and first is not None:
        target_name = first.exercise_name
        target_weight = first.weight_kg
    return ExtractedPrompt(
        kind=PromptKind(draft.kind),
        items=items,
        weeks=weeks,
        target_weight_kg=target_weight,
        target_exercise_name=target_name,
        declared_fatigue=draft.declared_fatigue,
        asks_substitution=draft.asks_substitution,
        unit=_prompt_unit(draft),
        raw_text=raw,
    )
