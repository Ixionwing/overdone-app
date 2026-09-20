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

API startup migrates Postgres and seeds `data/exercises.json` (mini free-exercise-db extract) when the catalog is empty. MiniLM weights live in the `hf_cache` volume.

Optional extract model:

```bash
docker compose --profile llm up --build
```

Then set `OLLAMA_BASE_URL=http://ollama:11434/v1` on the API service. Unset URL keeps the regex extractor.

## Local API (without Compose)

Postgres 16 + pgvector on `DATABASE_URL`. From `backend/`:

```bash
uv sync
alembic upgrade head
uv run python -m overdone.ingest
uv run uvicorn overdone.main:app --reload --port 8000
```

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
