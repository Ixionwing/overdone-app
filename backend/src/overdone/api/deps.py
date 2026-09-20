from collections.abc import AsyncIterator

from fastapi import HTTPException, Request
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    try:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except (OperationalError, OSError) as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
