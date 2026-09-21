from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from overdone.api.deps import ExtractSlot
from overdone.api.routers import baseline, evaluate, health
from overdone.boot import bootstrap_database
from overdone.config import Settings
from overdone.config import settings as default_settings
from overdone.db import create_engine, create_session_factory
from overdone.mcp.server import create_mcp
from overdone.services.extract_llm import extract_client_from_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or default_settings
    engine = create_engine(config.database_url)
    session_factory = create_session_factory(engine)
    extract_client = extract_client_from_settings(config)
    if extract_client is None:
        raise RuntimeError("OLLAMA_BASE_URL is required for prompt extraction")
    extract_slot = ExtractSlot(extract_client)
    mcp = create_mcp(session_factory, get_llm_client=lambda: extract_slot.client)
    mcp_http = mcp.http_app(path="/", transport="http")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await bootstrap_database(config, engine, session_factory)
        async with mcp_http.lifespan(app):
            yield
        await engine.dispose()

    app = FastAPI(title=config.app_name, lifespan=lifespan)
    app.state.settings = config
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.extract_slot = extract_slot
    app.state.extract_client = extract_client
    app.state.mcp = mcp
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(baseline.router, prefix="/api/v1")
    app.include_router(evaluate.router, prefix="/api/v1")
    app.mount("/mcp", mcp_http)
    return app


if (default_settings.ollama_base_url or "").strip():
    app = create_app()
else:
    app = FastAPI(title=default_settings.app_name)
