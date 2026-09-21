from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from fakes.extract_client import ScriptedExtractClient
from overdone.api.deps import set_extract_client
from overdone.config import Settings
from overdone.db import create_engine, create_session_factory
from overdone.ingest.catalog import seed_catalog
from overdone.ingest.embed import (
    load_embedding_fixture,
    recording_embeddings,
    save_embedding_fixture,
    use_real_embeddings,
)
from overdone.main import create_app

PG_ROOT = Path.home() / ".cache" / "overdone-pgsql" / "pgsql"
EMBED_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mini_embeddings.json"
MINI_CATALOG = Path(__file__).resolve().parent / "fixtures" / "exercises_mini.json"


@pytest.fixture(scope="session", autouse=True)
def embedding_fixture() -> Iterator[None]:
    if use_real_embeddings() and not recording_embeddings():
        yield
        return
    load_embedding_fixture(EMBED_FIXTURE, record=recording_embeddings())
    yield
    if recording_embeddings():
        save_embedding_fixture()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def postgres_url(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    if not (PG_ROOT / "bin" / "postgres").exists():
        pytest.skip("local PostgreSQL 16 binaries are not installed")

    data_dir = tmp_path_factory.mktemp("pgdata")
    port = _free_port()
    env = os.environ.copy()
    env["PATH"] = f"{PG_ROOT / 'bin'}:{env.get('PATH', '')}"
    compat = Path.home() / ".cache" / "overdone-pgsql" / "compat-lib"
    if compat.exists():
        env["LD_LIBRARY_PATH"] = f"{compat}:{env.get('LD_LIBRARY_PATH', '')}"
    subprocess.run(
        [
            str(PG_ROOT / "bin" / "initdb"),
            "-D",
            str(data_dir),
            "--username=overdone",
            "--auth=trust",
            "--no-locale",
            "--encoding=UTF8",
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    log_file = data_dir / "pg.log"
    subprocess.run(
        [
            str(PG_ROOT / "bin" / "pg_ctl"),
            "-D",
            str(data_dir),
            "-l",
            str(log_file),
            "-o",
            f"-p {port} -k {data_dir}",
            "start",
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )
    for _ in range(50):
        probe = subprocess.run(
            [
                str(PG_ROOT / "bin" / "pg_isready"),
                "-h",
                "127.0.0.1",
                "-p",
                str(port),
                "-U",
                "overdone",
            ],
            env=env,
            capture_output=True,
        )
        if probe.returncode == 0:
            break
        time.sleep(0.1)
    else:
        raise RuntimeError(f"postgres failed to start:\n{log_file.read_text()}")

    subprocess.run(
        [
            str(PG_ROOT / "bin" / "createdb"),
            "-h",
            "127.0.0.1",
            "-p",
            str(port),
            "-U",
            "overdone",
            "overdone",
        ],
        check=True,
        env=env,
    )
    url = f"postgresql+asyncpg://overdone@127.0.0.1:{port}/overdone"
    os.environ["DATABASE_URL"] = url
    from alembic import command
    from alembic.config import Config

    alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    yield url
    subprocess.run(
        [str(PG_ROOT / "bin" / "pg_ctl"), "-D", str(data_dir), "stop", "-m", "fast"],
        check=False,
        env=env,
        capture_output=True,
    )
    shutil.rmtree(data_dir, ignore_errors=True)


@pytest.fixture()
def client(postgres_url: str) -> Iterator[TestClient]:
    async def wipe() -> None:
        engine = create_engine(postgres_url)
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "TRUNCATE TABLE user_sets, user_sessions, "
                    "user_benchmarks, user_settings RESTART IDENTITY CASCADE"
                )
            )
            await connection.execute(
                text(
                    "DELETE FROM data_embeddings "
                    "WHERE metadata_->>'kind' = 'session_note'"
                )
            )
        await engine.dispose()

    asyncio.run(wipe())

    async def seed() -> None:
        engine = create_engine(postgres_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            await seed_catalog(session, json.loads(MINI_CATALOG.read_text()))
            await session.commit()
        await engine.dispose()

    asyncio.run(seed())
    settings = Settings(
        database_url=postgres_url,
        ollama_base_url="http://127.0.0.1:9/v1",
    )
    with TestClient(create_app(settings)) as test_client:
        app = test_client.app
        assert isinstance(app, FastAPI)
        set_extract_client(app, ScriptedExtractClient())
        yield test_client
