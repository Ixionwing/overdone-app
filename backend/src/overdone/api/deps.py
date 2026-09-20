from collections.abc import AsyncIterator

from fastapi import HTTPException, Request
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def get_extract_client(request: Request) -> object | None:
    return getattr(request.app.state, "extract_client", None)


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
