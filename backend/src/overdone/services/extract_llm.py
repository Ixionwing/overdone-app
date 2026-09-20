from __future__ import annotations

import asyncio

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from overdone.config import Settings
from overdone.schemas.dto import ExtractedPrompt

_INSTRUCTIONS = """Extract a workout increment from the user prompt.
Return structured fields only.
Use kind single_session unless the user names a future horizon
(next month, in N weeks) and a target load.
Convert named units to kilograms for weight_kg, delta_kg, and target_weight_kg.
Set unit to lb or kg when the user named one; otherwise null.
Copy fatigue phrasing into declared_fatigue.
Set asks_substitution true if they ask what to do instead.
Leave every exercise_id null. Do not invent catalog ids.
Do not coach or score.
"""


class PydanticAIExtractClient:
    def __init__(self, agent: Agent[None, ExtractedPrompt], *, timeout: float = 8.0):
        self._agent = agent
        self._timeout = timeout

    async def extract(self, text: str) -> ExtractedPrompt:
        async with asyncio.timeout(self._timeout):
            result = await self._agent.run(text)
        output = result.output
        if isinstance(output, ExtractedPrompt):
            return output
        return ExtractedPrompt.model_validate(output)


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
        output_type=ExtractedPrompt,
        instructions=_INSTRUCTIONS,
    )
    return PydanticAIExtractClient(agent)
