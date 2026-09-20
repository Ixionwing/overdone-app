from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from overdone.api.deps import get_extract_client, get_session
from overdone.schemas.api import EvaluateRequest
from overdone.schemas.dto import EvaluationResult
from overdone.services.evaluate import evaluate_prompt

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResult)
async def post_evaluate(
    payload: EvaluateRequest,
    session: AsyncSession = Depends(get_session),
    llm_client: object | None = Depends(get_extract_client),
) -> EvaluationResult:
    return await evaluate_prompt(session, payload.prompt, llm_client=llm_client)
