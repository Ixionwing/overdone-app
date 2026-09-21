from __future__ import annotations

import json
from pathlib import Path

from overdone.schemas.dto import ExtractedPrompt, LogSet, PromptKind, ProposedItem, Unit
from overdone.schemas.extract_draft import ExtractDraft
from overdone.services.evaluate import macro_sets_reps, resolve_macro_target_kg
from overdone.services.extract_llm import _FEWSHOT
from overdone.services.extract_map import to_extracted_prompt, weeks_from_raw
from overdone.services.units import lb_to_kg

GOLD = json.loads(
    (Path(__file__).resolve().parent / "fixtures" / "golden_extract.json").read_text()
)


def _row(prompt: str) -> dict:
    return next(item for item in GOLD if item["prompt"] == prompt)


def test_map_relative_add_20_lb_bench() -> None:
    row = _row("add 20 lb to bench tomorrow")
    extracted = to_extracted_prompt(
        ExtractDraft.model_validate(row["draft"]), row["prompt"]
    )
    assert extracted.kind is PromptKind.single_session
    assert extracted.unit is Unit.lb
    assert extracted.raw_text == row["prompt"]
    assert len(extracted.items) == 1
    item = extracted.items[0]
    assert "bench" in item.exercise_name.casefold()
    assert item.delta_kg is not None
    assert abs(item.delta_kg - lb_to_kg(20)) < 1e-6
    assert item.weight_kg is None


def test_map_absolute_pushdown() -> None:
    row = _row("bring pushdown up to 40 lb")
    extracted = to_extracted_prompt(
        ExtractDraft.model_validate(row["draft"]), row["prompt"]
    )
    item = extracted.items[0]
    assert item.weight_kg is not None
    assert abs(item.weight_kg - lb_to_kg(40)) < 1e-6
    assert item.delta_kg is None


def test_map_prescription_keeps_sets_reps() -> None:
    row = _row("3 sets of 8 @ 40lb on tricep pushdowns")
    extracted = to_extracted_prompt(
        ExtractDraft.model_validate(row["draft"]), row["prompt"]
    )
    item = extracted.items[0]
    assert item.sets == 3
    assert item.reps == 8
    assert item.weight_kg is not None


def test_map_macro_absolute_weeks() -> None:
    row = _row("i want to bench 225 by next month")
    extracted = to_extracted_prompt(
        ExtractDraft.model_validate(row["draft"]), row["prompt"]
    )
    assert extracted.kind is PromptKind.macro_goal
    assert extracted.weeks == 4
    assert extracted.target_exercise_name is not None
    assert "bench" in extracted.target_exercise_name.casefold()
    assert extracted.target_weight_kg is not None
    assert abs(extracted.target_weight_kg - lb_to_kg(225)) < 1e-6


def test_map_macro_delta_keeps_delta_item() -> None:
    row = _row("add 30 lbs to my deadlift in 6 weeks")
    extracted = to_extracted_prompt(
        ExtractDraft.model_validate(row["draft"]), row["prompt"]
    )
    assert extracted.kind is PromptKind.macro_goal
    assert extracted.weeks == 6
    assert extracted.target_weight_kg is None
    assert extracted.items[0].delta_kg is not None
    assert abs(extracted.items[0].delta_kg - lb_to_kg(30)) < 1e-6


def test_map_missing_unit_stays_none() -> None:
    row = _row("add 20 to bench tomorrow")
    extracted = to_extracted_prompt(
        ExtractDraft.model_validate(row["draft"]), row["prompt"]
    )
    assert extracted.unit is None
    assert extracted.items[0].delta_kg == 20


def test_map_weeks_from_raw_when_draft_omits() -> None:
    draft = ExtractDraft.model_validate(
        {
            "kind": "macro_goal",
            "items": [
                {
                    "name": "bench",
                    "amount": 225,
                    "amount_kind": "absolute",
                    "amount_unit": "lb",
                }
            ],
        }
    )
    extracted = to_extracted_prompt(draft, "i want to bench 225 by next month")
    assert extracted.weeks == 4


def test_weeks_from_raw_explicit_counts() -> None:
    assert weeks_from_raw("in 30 days") == 4
    assert weeks_from_raw("over 2 months") == 8
    assert weeks_from_raw("over the next 8 weeks") == 8


def test_resolve_macro_target_adds_delta_to_last() -> None:
    extracted = ExtractedPrompt(
        kind=PromptKind.macro_goal,
        items=[ProposedItem(exercise_name="deadlift", delta_kg=lb_to_kg(30))],
        weeks=6,
        target_exercise_name="deadlift",
        unit=Unit.lb,
        raw_text="add 30 lbs to my deadlift in 6 weeks",
    )
    last = lb_to_kg(185)
    target = resolve_macro_target_kg(extracted, last)
    assert target is not None
    assert abs(target - (last + lb_to_kg(30))) < 1e-6


def test_fewshot_rows_match_llm_examples() -> None:
    fewshot = [row for row in GOLD if row.get("fewshot")]
    assert len(fewshot) == 10
    llm = {prompt: draft for prompt, draft in _FEWSHOT}
    for row in fewshot:
        assert llm[row["prompt"]] == row["draft"]


def test_macro_sets_reps_prefers_named_prescription() -> None:
    extracted = ExtractedPrompt(
        kind=PromptKind.macro_goal,
        items=[
            ProposedItem(
                exercise_name="cable pushdown",
                weight_kg=lb_to_kg(35),
                sets=3,
                reps=8,
            )
        ],
        weeks=4,
        target_exercise_name="cable pushdown",
        unit=Unit.lb,
        raw_text="",
    )
    last = LogSet(
        exercise_name="Cable Pushdown",
        weight_kg=lb_to_kg(30),
        reps=10,
        sets=3,
    )
    assert macro_sets_reps(extracted, last) == (3, 8)


def test_macro_sets_reps_inherits_last_when_unnamed() -> None:
    extracted = ExtractedPrompt(
        kind=PromptKind.macro_goal,
        items=[],
        weeks=4,
        target_weight_kg=lb_to_kg(225),
        target_exercise_name="squat",
        unit=Unit.lb,
        raw_text="",
    )
    last = LogSet(
        exercise_name="Barbell Squat",
        weight_kg=lb_to_kg(185),
        reps=5,
        sets=3,
    )
    assert macro_sets_reps(extracted, last) == (3, 5)


def test_map_all_golden_rows() -> None:
    for row in GOLD:
        draft = ExtractDraft.model_validate(row["draft"])
        extracted = to_extracted_prompt(draft, row["prompt"])
        assert extracted.raw_text == row["prompt"]
        if draft.kind == "macro_goal":
            assert extracted.kind is PromptKind.macro_goal
            assert extracted.target_exercise_name
            assert extracted.weeks
            has_target = extracted.target_weight_kg is not None
            has_delta = any(item.delta_kg is not None for item in extracted.items)
            assert has_target or has_delta
        else:
            assert extracted.kind is PromptKind.single_session
            assert extracted.items
