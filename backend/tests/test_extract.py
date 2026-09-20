from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError
from pydantic_ai import UnexpectedModelBehavior

from overdone.config import Settings
from overdone.schemas.dto import ExtractedPrompt, PromptKind, ProposedItem, Unit
from overdone.services.extract import extract_prompt
from overdone.services.extract_llm import extract_client_from_settings


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


class _BrokenExtractor:
    async def extract(self, text: str):
        raise RuntimeError("extractor bug")


def test_unexpected_extractor_error_propagates():
    with pytest.raises(RuntimeError, match="extractor bug"):
        asyncio.run(
            extract_prompt(
                "Add 20 lbs to Bench tomorrow.",
                llm_client=_BrokenExtractor(),
            )
        )


class _TimeoutExtractor:
    async def extract(self, text: str):
        raise TimeoutError


def test_timeout_falls_back_to_heuristic():
    result = asyncio.run(
        extract_prompt(
            "Add 20 lbs to Bench tomorrow.",
            llm_client=_TimeoutExtractor(),
        )
    )
    assert len(result.items) == 1
    assert result.items[0].delta_kg is not None
    assert abs(result.items[0].delta_kg - 9.0718474) < 1e-6


class _InvalidExtractor:
    async def extract(self, text: str):
        raise ValidationError.from_exception_data("ExtractedPrompt", [])


def test_invalid_structured_output_falls_back_to_heuristic():
    result = asyncio.run(
        extract_prompt(
            "Add 20 lbs to Bench tomorrow.",
            llm_client=_InvalidExtractor(),
        )
    )
    assert len(result.items) == 1
    assert "bench" in result.items[0].exercise_name.casefold()


class _ModelErrorExtractor:
    async def extract(self, text: str):
        raise UnexpectedModelBehavior("not json")


def test_model_behavior_error_falls_back_to_heuristic():
    result = asyncio.run(
        extract_prompt(
            "Add 20 lbs to Bench tomorrow.",
            llm_client=_ModelErrorExtractor(),
        )
    )
    assert len(result.items) == 1


class _FixedExtractor:
    async def extract(self, text: str) -> ExtractedPrompt:
        return ExtractedPrompt(
            kind=PromptKind.single_session,
            items=[
                ProposedItem(
                    exercise_name="custom nick",
                    delta_kg=9.07,
                    exercise_id="invented",
                )
            ],
            unit=Unit.lb,
            raw_text=text,
        )


def test_llm_extract_is_used_and_catalog_ids_are_stripped():
    result = asyncio.run(extract_prompt("bump the press", llm_client=_FixedExtractor()))
    assert result.items[0].exercise_name == "custom nick"
    assert result.items[0].delta_kg == 9.07
    assert result.items[0].exercise_id is None


def test_unset_ollama_url_builds_no_client():
    assert extract_client_from_settings(Settings(ollama_base_url=None)) is None
    assert extract_client_from_settings(Settings(ollama_base_url="  ")) is None


def test_ollama_url_builds_extract_client():
    client = extract_client_from_settings(
        Settings(ollama_base_url="http://127.0.0.1:9/v1")
    )
    assert client is not None
    assert callable(client.extract)
