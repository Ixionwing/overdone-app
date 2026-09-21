from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class ExtractSlot:
    def __init__(self, client: object) -> None:
        self.client = client


def get_extract_client(request: Request) -> object | None:
    slot = getattr(request.app.state, "extract_slot", None)
    if isinstance(slot, ExtractSlot):
        return slot.client
    return getattr(request.app.state, "extract_client", None)


def set_extract_client(app: FastAPI, client: object) -> None:
    slot = getattr(app.state, "extract_slot", None)
    if isinstance(slot, ExtractSlot):
        slot.client = client
    app.state.extract_client = client


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    try:
        async with factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    except (OperationalError, OSError) as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
