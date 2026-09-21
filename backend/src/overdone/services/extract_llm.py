from __future__ import annotations

import asyncio
import json

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.output import NativeOutput
from pydantic_ai.providers.openai import OpenAIProvider

from overdone.config import Settings
from overdone.schemas.extract_draft import ExtractDraft
from overdone.services.extract_gold import fewshot_examples


def _fewshot_block() -> str:
    parts = []
    for prompt, draft in fewshot_examples():
        parts.append(f"User: {prompt}\n{json.dumps(draft, separators=(',', ':'))}")
    return "\n\n".join(parts)


_INSTRUCTIONS = f"""Extract a workout increment from the user prompt.
Return structured JSON matching ExtractDraft only.

kind:
- single_session: the next workout (tomorrow, this session, no horizon).
- macro_goal: a future horizon plus a target load
  (next month, in a month, over the next N weeks, in N weeks).

items: one object per named lift. Keep the user's nickname (OHP, DB bench).
amount is the spoken number. Do not convert lb/kg.
amount_kind: delta (add/drop/bump), absolute (up to / @ load), extra_sets.
amount_unit: "lb" or "kg" only when the user named one; otherwise omit.
sets and reps only when a prescription is named (NxM, N sets of M).
extra_sets: put the extra set count in amount; omit amount_unit.

For macro_goal set weeks (a month / next month = 4, N months = N*4, 30 days = 4)
and exactly one item. Relative macros still use amount_kind=delta.

Copy fatigue phrasing into declared_fatigue.
Set asks_substitution true if they ask what to do instead.
Omit unused fields. Never emit the string "null".
Do not invent catalog ids or kilograms.
Do not coach or score.

Examples:
{_fewshot_block()}
"""


class PydanticAIExtractClient:
    def __init__(self, agent: Agent[None, ExtractDraft], *, timeout: float = 30.0):
        self._agent = agent
        self.timeout = timeout

    async def extract(self, text: str) -> ExtractDraft:
        async with asyncio.timeout(self.timeout):
            result = await self._agent.run(text)
        output = result.output
        if isinstance(output, ExtractDraft):
            return output
        return ExtractDraft.model_validate(output)


def extract_client_from_settings(
    settings: Settings,
) -> PydanticAIExtractClient | None:
    url = (settings.ollama_base_url or "").strip() or None
    if url is None:
        return None
    model = OpenAIChatModel(
        settings.ollama_model,
        provider=OpenAIProvider(base_url=url, api_key="ollama"),
    )
    agent = Agent(
        model,
        output_type=NativeOutput(ExtractDraft),
        instructions=_INSTRUCTIONS,
        retries=3,
    )
    return PydanticAIExtractClient(agent, timeout=settings.ollama_timeout_seconds)
