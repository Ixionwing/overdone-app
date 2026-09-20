from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from overdone.api.deps import get_session

router = APIRouter()


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok"}
