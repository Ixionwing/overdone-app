from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from overdone.api.routers import baseline, evaluate, health
from overdone.config import Settings
from overdone.config import settings as default_settings
from overdone.db import create_engine, create_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or default_settings
    engine = create_engine(config.database_url)
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await engine.dispose()

    app = FastAPI(title=config.app_name, lifespan=lifespan)
    app.state.settings = config
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(baseline.router, prefix="/api/v1")
    app.include_router(evaluate.router, prefix="/api/v1")
    return app


app = create_app()
