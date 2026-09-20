# syntax=docker/dockerfile:1

FROM python:3.12.11-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.12.11-slim-bookworm AS runtime

RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"

USER app

EXPOSE 8000

CMD ["uvicorn", "overdone.main:app", "--host", "0.0.0.0", "--port", "8000"]
