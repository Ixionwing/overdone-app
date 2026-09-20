from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from overdone.api.deps import get_session
from overdone.schemas.api import EvaluateRequest
from overdone.schemas.dto import EvaluationResult
from overdone.services.evaluate import evaluate_prompt

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResult)
async def post_evaluate(
    payload: EvaluateRequest, session: AsyncSession = Depends(get_session)
) -> EvaluationResult:
    return await evaluate_prompt(session, payload.prompt)
