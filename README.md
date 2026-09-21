# Overdone

Local scratchpad: import a training baseline, propose a workout increment in plain language, get Green/Yellow/Red plus gauges. Evaluations are not stored. Same evaluate is available over HTTP and MCP.

## Run (Compose)

```bash
cp .env.example .env   # optional; Compose already sets API env
docker compose up --build
```

- UI: http://localhost:3000
- API: http://localhost:8000/health
- MCP: http://localhost:8000/mcp

API startup migrates Postgres and seeds `data/free-exercise-db/exercises.json` (yuhonas/free-exercise-db, Unlicense) when the catalog is empty. MiniLM weights live in the `hf_cache` volume. Tests still use the mini fixture.

Extract requires a local OpenAI-compatible server (`OLLAMA_BASE_URL`). Host Ollama is enough; Compose can still start a container with `docker compose --profile llm up --build` and `OLLAMA_BASE_URL=http://ollama:11434/v1` on the API. There is no regex extractor — the API will not start if the URL is unset.

## Local API (without Compose)

Postgres 16 + pgvector on `DATABASE_URL`. From `backend/`:

```bash
uv sync
alembic upgrade head
uv run python -m overdone.ingest
uv run uvicorn overdone.main:app --reload --port 8000
```

Set `OLLAMA_BASE_URL=http://127.0.0.1:11434/v1` (and `OLLAMA_MODEL=llama3.2`) before starting the API.

Frontend: `cd frontend && npm ci && npm run dev`.

## Tests

```bash
cd backend && uv run pytest -v
cd frontend && npx tsc --noEmit
```

Pytest uses a fixture embedding map and does not download MiniLM or call Ollama.

## Specs

- Product: `product-spec.md`
- Technical: `docs/technical-spec.md`
- Slice plan: `docs/implementation-plan.md`
