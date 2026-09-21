from __future__ import annotations

import inspect
import logging

from pydantic import ValidationError
from pydantic_ai import AgentRunError, UnexpectedModelBehavior

from overdone.schemas.dto import ExtractedPrompt, PromptKind
from overdone.schemas.extract_draft import ExtractDraft
from overdone.services.extract_map import to_extracted_prompt

logger = logging.getLogger(__name__)

_LLM_FAILURE = (
    TimeoutError,
    ConnectionError,
    OSError,
    ValidationError,
    AgentRunError,
    UnexpectedModelBehavior,
)


class ExtractError(Exception):
    """Structured extract failed or produced nothing scorable."""


def _without_catalog_ids(extracted: ExtractedPrompt) -> ExtractedPrompt:
    items = [item.model_copy(update={"exercise_id": None}) for item in extracted.items]
    return extracted.model_copy(update={"items": items})


def _macro_is_scorable(extracted: ExtractedPrompt) -> bool:
    name = (extracted.target_exercise_name or "").strip()
    if not name:
        return False
    if extracted.target_weight_kg is not None:
        return True
    return any(item.delta_kg is not None for item in extracted.items)


async def extract_prompt(text: str, *, llm_client: object | None) -> ExtractedPrompt:
    extract = getattr(llm_client, "extract", None) if llm_client is not None else None
    if not callable(extract):
        raise ExtractError("extract client is required")
    try:
        result = extract(text)
        if inspect.isawaitable(result):
            result = await result
    except _LLM_FAILURE as exc:
        logger.warning("llm extract failed", exc_info=True)
        raise ExtractError("llm extract failed") from exc
    if isinstance(result, ExtractDraft):
        result = to_extracted_prompt(result, text)
    if not isinstance(result, ExtractedPrompt):
        raise ExtractError("llm extract returned an invalid payload")
    cleaned = _without_catalog_ids(result).model_copy(update={"raw_text": text})
    if cleaned.kind is PromptKind.macro_goal:
        if _macro_is_scorable(cleaned):
            return cleaned
        raise ExtractError("macro extract is missing a target")
    if cleaned.items:
        return cleaned
    raise ExtractError("session extract has no items")
