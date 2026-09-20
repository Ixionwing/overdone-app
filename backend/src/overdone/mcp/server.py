from __future__ import annotations

from fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from overdone.schemas.api import BaselineImport
from overdone.services.baseline import (
    get_baseline,
    replace_baseline,
    replace_baseline_from_text,
)
from overdone.services.evaluate import evaluate_prompt as run_evaluate


def create_mcp(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    llm_client: object | None = None,
) -> FastMCP:
    mcp = FastMCP("Overdone")

    @mcp.tool
    async def get_baseline_status() -> dict:
        async with session_factory() as session:
            status = await get_baseline(session)
            return status.model_dump(mode="json")

    @mcp.tool
    async def replace_baseline_json(payload: str) -> dict:
        data = BaselineImport.model_validate_json(payload)
        async with session_factory() as session:
            status = await replace_baseline(session, data)
            return status.model_dump(mode="json")

    @mcp.tool
    async def replace_baseline_text(text: str) -> dict:
        async with session_factory() as session:
            status = await replace_baseline_from_text(session, text)
            return status.model_dump(mode="json")

    @mcp.tool
    async def evaluate_prompt(prompt: str) -> dict:
        async with session_factory() as session:
            result = await run_evaluate(session, prompt, llm_client=llm_client)
            return result.model_dump(mode="json")

    return mcp
