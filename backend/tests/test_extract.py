from __future__ import annotations

import asyncio

from overdone.schemas.dto import PromptKind, Unit
from overdone.services.extract import extract_prompt


def _extract(text: str):
    return asyncio.run(extract_prompt(text, llm_client=None))


def test_add_20_lbs_to_db_bench():
    result = _extract("Add 20 lbs to DB Bench Press tomorrow.")
    assert result.kind is PromptKind.single_session
    assert len(result.items) == 1
    assert result.unit is Unit.lb
    assert result.items[0].delta_kg is not None
    assert abs(result.items[0].delta_kg - 9.0718474) < 1e-6
    assert "bench" in result.items[0].exercise_name.casefold()


def test_multi_movement_prompt():
    result = _extract(
        "Tomorrow: +10 lbs Bench, +5 lbs Incline DB Press, +3 sets Pushdowns."
    )
    assert result.kind is PromptKind.single_session
    assert len(result.items) == 3
    names = [item.exercise_name.casefold() for item in result.items]
    assert any("bench" in name for name in names)
    assert any("incline" in name for name in names)
    assert any("pushdown" in name for name in names)
    extras = [item.extra_sets for item in result.items if item.extra_sets]
    assert extras == [3]


def test_macro_225_squat_next_month():
    result = _extract("Reach a 225 lb Squat by next month.")
    assert result.kind is PromptKind.macro_goal
    assert result.weeks == 4
    assert result.unit is Unit.lb
    assert result.target_exercise_name is not None
    assert "squat" in result.target_exercise_name.casefold()
    assert result.target_weight_kg is not None
    assert abs(result.target_weight_kg - 102.05828325) < 1e-6


def test_fatigue_clause_copied():
    result = _extract("Slept 4 hours, but want to add 10 lbs to Bench tomorrow.")
    assert result.declared_fatigue is not None
    assert "slept 4 hours" in result.declared_fatigue.casefold()
    assert len(result.items) == 1


def test_substitution_flag():
    result = _extract("Add 30 lbs to Bench tomorrow, or tell me what to do instead.")
    assert result.asks_substitution is True
    assert len(result.items) == 1


def test_missing_unit_stays_none():
    result = _extract("Add 200 to Bench tomorrow.")
    assert result.unit is None
    assert result.items[0].delta_kg == 200
