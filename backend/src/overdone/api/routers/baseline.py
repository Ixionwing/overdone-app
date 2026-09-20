import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from overdone.api.deps import get_session
from overdone.schemas.api import BaselineImport, BaselineStatus, BaselineTextImport
from overdone.services.baseline import (
    get_baseline,
    replace_baseline,
    replace_baseline_from_text,
)

router = APIRouter()


@router.get("/baseline", response_model=BaselineStatus)
async def read_baseline(session: AsyncSession = Depends(get_session)) -> BaselineStatus:
    return await get_baseline(session)


@router.put("/baseline", response_model=BaselineStatus)
async def put_baseline(
    payload: BaselineImport, session: AsyncSession = Depends(get_session)
) -> BaselineStatus:
    return await replace_baseline(session, payload)


@router.post("/baseline/text", response_model=BaselineStatus)
async def put_baseline_text(
    payload: BaselineTextImport, session: AsyncSession = Depends(get_session)
) -> BaselineStatus:
    try:
        return await replace_baseline_from_text(session, payload.text)
    except (ValueError, ValidationError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
