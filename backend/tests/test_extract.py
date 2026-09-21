from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError
from pydantic_ai import UnexpectedModelBehavior

from overdone.config import Settings
from overdone.main import create_app
from overdone.schemas.dto import ExtractedPrompt, PromptKind, ProposedItem, Unit
from overdone.schemas.extract_draft import ExtractDraft
from overdone.services.extract import ExtractError, extract_prompt
from overdone.services.extract_llm import extract_client_from_settings


class _BrokenExtractor:
    async def extract(self, text: str):
        raise RuntimeError("extractor bug")


class _TimeoutExtractor:
    async def extract(self, text: str):
        raise TimeoutError


class _InvalidExtractor:
    async def extract(self, text: str):
        raise ValidationError.from_exception_data("ExtractedPrompt", [])


class _ModelErrorExtractor:
    async def extract(self, text: str):
        raise UnexpectedModelBehavior("not json")


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


def test_missing_client_raises_extract_error():
    with pytest.raises(ExtractError):
        asyncio.run(extract_prompt("add 20 lbs to bench", llm_client=None))


def test_timeout_raises_extract_error():
    with pytest.raises(ExtractError):
        asyncio.run(
            extract_prompt("add 20 lbs to bench", llm_client=_TimeoutExtractor())
        )


def test_empty_session_extract_raises_extract_error():
    class EmptyExtractor:
        async def extract(self, text: str) -> ExtractedPrompt:
            return ExtractedPrompt(
                kind=PromptKind.single_session, items=[], raw_text=text
            )

    with pytest.raises(ExtractError):
        asyncio.run(
            extract_prompt("get to 3 sets of 8 @ 40lb", llm_client=EmptyExtractor())
        )


def test_valid_macro_without_items_is_kept():
    class MacroExtractor:
        async def extract(self, text: str) -> ExtractedPrompt:
            return ExtractedPrompt(
                kind=PromptKind.macro_goal,
                items=[],
                weeks=4,
                target_weight_kg=18.1436948,
                target_exercise_name="cable pushdown",
                unit=Unit.lb,
                raw_text=text,
            )

    result = asyncio.run(
        extract_prompt("over the next 4 weeks", llm_client=MacroExtractor())
    )
    assert result.kind is PromptKind.macro_goal
    assert result.weeks == 4


def test_macro_missing_target_raises_extract_error():
    class IncompleteMacro:
        async def extract(self, text: str) -> ExtractedPrompt:
            return ExtractedPrompt(
                kind=PromptKind.macro_goal,
                items=[],
                weeks=4,
                raw_text=text,
            )

    with pytest.raises(ExtractError):
        asyncio.run(extract_prompt("in a month", llm_client=IncompleteMacro()))


def test_unexpected_extractor_error_propagates():
    with pytest.raises(RuntimeError, match="extractor bug"):
        asyncio.run(
            extract_prompt(
                "Add 20 lbs to Bench tomorrow.",
                llm_client=_BrokenExtractor(),
            )
        )


def test_invalid_structured_output_raises_extract_error():
    with pytest.raises(ExtractError):
        asyncio.run(
            extract_prompt(
                "Add 20 lbs to Bench tomorrow.",
                llm_client=_InvalidExtractor(),
            )
        )


def test_model_behavior_error_raises_extract_error():
    with pytest.raises(ExtractError):
        asyncio.run(
            extract_prompt(
                "Add 20 lbs to Bench tomorrow.",
                llm_client=_ModelErrorExtractor(),
            )
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


def test_extract_client_uses_timeout_seconds():
    client = extract_client_from_settings(
        Settings(
            ollama_base_url="http://127.0.0.1:9/v1",
            ollama_timeout_seconds=30.0,
        )
    )
    assert client is not None
    assert client.timeout == 30.0


def test_create_app_requires_ollama_url() -> None:
    with pytest.raises(RuntimeError, match="OLLAMA_BASE_URL"):
        create_app(
            Settings(
                database_url="postgresql+asyncpg://overdone@127.0.0.1:1/overdone",
                ollama_base_url=None,
            )
        )


def test_proposed_item_coerces_null_strings() -> None:
    item = ProposedItem.model_validate(
        {
            "exercise_name": "bench press",
            "reps": "null",
            "sets": "null",
            "extra_sets": "null",
            "exercise_id": "null",
        }
    )
    assert item.reps is None
    assert item.sets is None
    assert item.extra_sets is None
    assert item.exercise_id is None


def test_extract_prompt_maps_draft() -> None:
    class DraftExtractor:
        async def extract(self, text: str) -> ExtractDraft:
            return ExtractDraft.model_validate(
                {
                    "kind": "single_session",
                    "items": [
                        {
                            "name": "bench",
                            "amount": 20,
                            "amount_kind": "delta",
                            "amount_unit": "lb",
                        }
                    ],
                }
            )

    result = asyncio.run(
        extract_prompt("add 20 lb to bench tomorrow", llm_client=DraftExtractor())
    )
    assert result.kind is PromptKind.single_session
    assert result.unit is Unit.lb
    assert result.items[0].exercise_name == "bench"
    assert result.items[0].delta_kg is not None
    assert result.raw_text == "add 20 lb to bench tomorrow"


def test_extract_prompt_keeps_macro_delta_draft() -> None:
    class DraftExtractor:
        async def extract(self, text: str) -> ExtractDraft:
            return ExtractDraft.model_validate(
                {
                    "kind": "macro_goal",
                    "weeks": 6,
                    "items": [
                        {
                            "name": "deadlift",
                            "amount": 30,
                            "amount_kind": "delta",
                            "amount_unit": "lb",
                        }
                    ],
                }
            )

    result = asyncio.run(
        extract_prompt(
            "add 30 lbs to my deadlift in 6 weeks", llm_client=DraftExtractor()
        )
    )
    assert result.kind is PromptKind.macro_goal
    assert result.weeks == 6
    assert result.target_weight_kg is None
    assert result.items[0].delta_kg is not None


def test_extracted_prompt_drops_relative_target_date() -> None:
    extracted = ExtractedPrompt.model_validate(
        {
            "kind": "single_session",
            "items": [{"exercise_name": "Bench", "delta_kg": 9.07}],
            "target_date": "tomorrow",
        }
    )
    assert extracted.target_date is None
    assert extracted.raw_text == ""
