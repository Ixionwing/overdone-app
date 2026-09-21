from __future__ import annotations

import asyncio
import json

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.output import NativeOutput
from pydantic_ai.providers.openai import OpenAIProvider

from overdone.config import Settings
from overdone.schemas.extract_draft import ExtractDraft

_FEWSHOT: list[tuple[str, dict]] = [
    (
        "add 20 lb to bench tomorrow",
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
        },
    ),
    (
        "bring pushdown up to 40 lb",
        {
            "kind": "single_session",
            "items": [
                {
                    "name": "pushdown",
                    "amount": 40,
                    "amount_kind": "absolute",
                    "amount_unit": "lb",
                }
            ],
        },
    ),
    (
        "3 sets of 8 @ 40lb on tricep pushdowns",
        {
            "kind": "single_session",
            "items": [
                {
                    "name": "tricep pushdowns",
                    "amount": 40,
                    "amount_kind": "absolute",
                    "amount_unit": "lb",
                    "sets": 3,
                    "reps": 8,
                }
            ],
        },
    ),
    (
        "i want to bench 225 by next month",
        {
            "kind": "macro_goal",
            "weeks": 4,
            "items": [
                {
                    "name": "bench",
                    "amount": 225,
                    "amount_kind": "absolute",
                    "amount_unit": "lb",
                }
            ],
        },
    ),
    (
        "+10 bench, +5 incline, +3 sets pushdowns tomorrow",
        {
            "kind": "single_session",
            "items": [
                {
                    "name": "bench",
                    "amount": 10,
                    "amount_kind": "delta",
                    "amount_unit": "lb",
                },
                {
                    "name": "incline",
                    "amount": 5,
                    "amount_kind": "delta",
                    "amount_unit": "lb",
                },
                {
                    "name": "pushdowns",
                    "amount": 3,
                    "amount_kind": "extra_sets",
                },
            ],
        },
    ),
    (
        "bring OHP to 135 tomorrow",
        {
            "kind": "single_session",
            "items": [
                {
                    "name": "OHP",
                    "amount": 135,
                    "amount_kind": "absolute",
                    "amount_unit": "lb",
                }
            ],
        },
    ),
    (
        "only slept 4 hours and feel beat up, "
        "but I want to add 10 lbs to bench tomorrow",
        {
            "kind": "single_session",
            "declared_fatigue": "only slept 4 hours and feel beat up",
            "items": [
                {
                    "name": "bench",
                    "amount": 10,
                    "amount_kind": "delta",
                    "amount_unit": "lb",
                }
            ],
        },
    ),
    (
        "i want to add 30 lbs to my bench press tomorrow, "
        "or tell me what to do instead",
        {
            "kind": "single_session",
            "asks_substitution": True,
            "items": [
                {
                    "name": "bench press",
                    "amount": 30,
                    "amount_kind": "delta",
                    "amount_unit": "lb",
                }
            ],
        },
    ),
    (
        "add 20 to bench tomorrow",
        {
            "kind": "single_session",
            "items": [
                {
                    "name": "bench",
                    "amount": 20,
                    "amount_kind": "delta",
                }
            ],
        },
    ),
    (
        "add 30 lbs to my deadlift in 6 weeks",
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
        },
    ),
]


def _fewshot_block() -> str:
    parts = []
    for prompt, draft in _FEWSHOT:
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
