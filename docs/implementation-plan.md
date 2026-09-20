# Overdone POC Implementation Plan

> Execute **one slice at a time**. A slice is done only when its demo and verification commands have been run. Prefer TDD inside a slice: one failing test, minimal code, pass. Do not start the next slice until the current slice’s demo works.

**Goal:** Ship a local Compose stack (Postgres/pgvector + FastAPI/FastMCP + Next.js) that ingests a static training baseline, evaluates a natural-language workout increment, and returns Green/Yellow/Red plus gauges without storing prompt history.

**Architecture:** One FastAPI process owns HTTP and mounted FastMCP. LlamaIndex writes exercise (and note) embeddings to pgvector; `retrieve_context` reads them over SQL. Scoring and narratives are pure Python. Baseline is the only user write.

**Tech stack:** Python 3.12, FastAPI, FastMCP, SQLAlchemy 2.x, Alembic, LlamaIndex ingest writer, optional Pydantic AI extractor, sentence-transformers `all-MiniLM-L6-v2`, PostgreSQL 16 + pgvector, Next.js App Router, Docker Compose.

**Companion spec:** `docs/technical-spec.md`. `product-spec.md` wins on product behavior.

**Confirmed:** optional Ollama + heuristic fallback; Next.js UI; no auth.

## Slices (do these in order)

Each slice leaves a running app that is more useful than the last. Catalog/RAG and MCP come *after* a human can already get a traffic light in the browser.

| Slice | You can demo | Not in this slice |
| :--- | :--- | :--- |
| **A — Walking skeleton** | `docker compose up`; UI shows API/DB health | Baseline, scoring |
| **B — Baseline scratchpad** | Paste/upload JSON or text; refresh still shows the log | Evaluate |
| **C — Traffic lights** | Prompt → Green/Yellow/Red, gauges, halt/fatigue/scope | Fuzzy names, note retrieval, MCP |
| **D — Catalog + RAG** | “DB Bench” resolves; shoulder-note banner; enrichment factors | MCP |
| **E — MCP + DoD** | Same evaluate via `/mcp`; full product DoD | — |

Slice C uses a **stub resolver**: casefold / alias match against names already in the user’s baseline (and a tiny built-in alias list). Slice D replaces that stub with catalog embeddings. Do not wait on MiniLM to ship a verdict UI.

```
A  skeleton
B  baseline persist ─────────────────────┐
C  extract + score + evaluate HTTP + UI ─┼─► usable scratchpad
D  seed + embed + retrieve ──────────────┤
E  MCP + compose seed-on-boot ───────────┘
```

Tasks 3–4 (pure scoring/extract) have no DB and may be written during Slice B, but they must not be *wired* to HTTP until Slice C.

## Global constraints

- Python 3.12; Postgres 16 + pgvector; embeddings 384-d MiniLM local only.
- Canonical mass unit kg; `1 lb = 0.45359237 kg`.
- Ruff (`I`, `UP` + format) and Pyright `standard` on the backend; ESLint + Prettier + `tsc --noEmit` strict on the frontend. Do not add a parallel linter stack.
- FastMCP mounted on FastAPI; tools call services; no second ingest path.
- Evaluate is read-only. No evaluations table. No auth.
- Tests: no network; no SQLite stand-in for pgvector. Scoring tests are pure unit tests.
- Dockerfiles start with `# syntax=docker/dockerfile:1`, non-root `USER`, pinned tags.
- Do not read or commit `.env` / `.env.production`.

## File map (locked)

Create these as the tasks below name them. Do not invent a second layout.

```
compose.yaml
.env.example
.gitignore                         # extend for node, next, .env
backend/Dockerfile
backend/.dockerignore
backend/pyproject.toml
backend/alembic.ini
backend/alembic/env.py
backend/alembic/versions/*        # Alembic-generated only
backend/src/overdone/main.py
backend/src/overdone/config.py
backend/src/overdone/db.py
backend/src/overdone/api/deps.py
backend/src/overdone/api/routers/health.py
backend/src/overdone/api/routers/baseline.py
backend/src/overdone/api/routers/evaluate.py
backend/src/overdone/models/base.py
backend/src/overdone/models/exercise.py
backend/src/overdone/models/user_log.py
backend/src/overdone/schemas/dto.py
backend/src/overdone/schemas/api.py
backend/src/overdone/services/units.py
backend/src/overdone/services/scoring.py
backend/src/overdone/services/narrative.py
backend/src/overdone/services/extract.py
backend/src/overdone/services/resolve.py
backend/src/overdone/services/baseline.py
backend/src/overdone/services/retrieve.py
backend/src/overdone/services/evaluate.py
backend/src/overdone/ingest/catalog.py
backend/src/overdone/mcp/server.py
backend/tests/conftest.py
backend/tests/test_scoring.py
backend/tests/test_narrative.py
backend/tests/test_extract.py
backend/tests/test_resolve.py
backend/tests/test_baseline_api.py
backend/tests/test_evaluate_api.py
backend/tests/test_catalog_ingest.py
backend/tests/test_retrieve.py
backend/tests/test_mcp.py
frontend/Dockerfile
frontend/.dockerignore
frontend/package.json
frontend/src/app/page.tsx
frontend/src/app/globals.css
frontend/src/lib/api.ts
frontend/src/lib/types.ts
frontend/src/components/StatusBar.tsx
frontend/src/components/BaselinePanel.tsx
frontend/src/components/PromptPanel.tsx
frontend/src/components/VerdictPanel.tsx
data/enrichment_rules.json
data/sample_baseline.json
data/free-exercise-db/exercises.json   # vendored dist extract or download script
```

---

# Slice A — Walking skeleton

**Demo:** API + UI locally (Compose files are in the repo; Docker CLI was not available when this slice was implemented). Browser shows API reachable and `{"status":"ok"}`.

**Slice DoD**

- [x] `GET /health` returns `{"status":"ok"}` (uvicorn; DB ping is Slice B)
- [x] `GET /health` is 503 if the DB is down (Slice B)
- [x] UI loads and displays that health payload
- [x] `ruff check` / health pytest pass; frontend `tsc --noEmit` passes
- [ ] `docker compose up --build --wait` once Docker is installed

Stop when the one-panel status page works. No baseline form yet.

### Task A1: Compose Postgres + backend skeleton + health

**Files:**
- Create: `compose.yaml`, `.env.example`, `backend/pyproject.toml`, `backend/Dockerfile`, `backend/.dockerignore`, `backend/src/overdone/main.py`, `backend/src/overdone/config.py`, `backend/src/overdone/api/routers/health.py`, `backend/tests/test_health.py`
- Modify: `.gitignore` (add `node_modules/`, `.next/`, `frontend/.env*`)

**Interfaces:**
- Produces: `create_app() -> FastAPI` with `GET /health` → `{"status": "ok"}` without DB in this task.
- Consumes: nothing.

- [ ] **Step 1: Failing health test**

```python
from fastapi.testclient import TestClient
from overdone.main import create_app

def test_health_ok():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run to see fail**

```bash
cd backend && pytest tests/test_health.py -v
```

Expected: import or 404 failure.

- [ ] **Step 3: Minimal FastAPI app + Ruff/Pyright config in `pyproject.toml`** (ruff `I`+`UP`, pyright standard). `create_app()` registers the health router.

- [ ] **Step 4: Re-run pytest** — pass.

- [ ] **Step 5: `compose.yaml`** with `db` and `api`. Pin `pgvector/pgvector:pg16`. Postgres healthcheck: `pg_isready -U overdone`. API Dockerfile: syntax directive, non-root user, copy lock/pyproject before src.

Verify:

```bash
cd backend && ruff check . && ruff format --check . && pytest tests/test_health.py -v
docker compose up -d db --wait
```

Expected: ruff clean, tests pass, db healthy.

### Task A2: Next.js shell + health status

**Files:**
- Create: `frontend/` App Router app (TS strict, ESLint + Prettier), `frontend/src/lib/api.ts` (`getHealth`), `frontend/src/components/StatusBar.tsx`, `frontend/src/app/page.tsx`, `frontend/Dockerfile`
- Modify: `compose.yaml` add `web`

**Interfaces:**
- Produces: page fetches `GET /health` on load (or a tiny server component fetch) and shows ok / error. No other panels.

Verify: `cd frontend && npx tsc --noEmit`; Compose `web` + `api` + `db`; browser shows healthy. If browser tools are unavailable, `curl` health and say UI was typechecked only.

---

# Slice B — Baseline scratchpad

**Demo:** Paste `data/sample_baseline.json` (or a short text log), save, refresh; session/benchmark counts remain. API + UI were verified locally against PostgreSQL 16 + pgvector (user-space binaries; Compose still needs Docker).

**Slice DoD**

- [x] `PUT /api/v1/baseline` replaces history (second PUT does not append)
- [x] `POST /api/v1/baseline/text` accepts the sample text shape
- [x] `GET /api/v1/baseline` round-trips notes
- [x] UI baseline box: textarea, JSON file input, counts, error string
- [x] Postgres `vector` extension exists even if unused until Slice D
- [x] `GET /health` pings DB (`200` when up, `503` when unreachable)

### Task B1: SQLAlchemy models + Alembic + `vector` extension

**Files:**
- Create: `backend/src/overdone/db.py`, `backend/src/overdone/models/base.py`, `backend/src/overdone/models/exercise.py`, `backend/src/overdone/models/user_log.py`, `backend/alembic.ini`, `backend/alembic/env.py`, first Alembic revision
- Modify: `backend/src/overdone/config.py` (`DATABASE_URL`), `backend/src/overdone/api/deps.py`, `health` router (DB ping)

**Interfaces:**
- Consumes: `DATABASE_URL` asyncpg URL.
- Produces: `get_session() -> AsyncIterator[AsyncSession]` (`expire_on_commit=False`); models in technical spec §5.3; Alembic upgrade creates `vector` and tables.

`MetaData` naming_convention required. Relationships `lazy="raise"`. Revision must use `sa.table` / op SQL, not import live ORM models.

- [ ] **Step 1: Migration smoke**

```bash
docker compose exec api alembic upgrade head
docker compose exec db psql -U overdone -d overdone -c "\dx"
docker compose exec db psql -U overdone -d overdone -c "\dt"
```

Expected: `vector` listed; `exercises`, `exercise_enrichment`, `exercise_aliases`, `data_embeddings`, `user_benchmarks`, `user_sessions`, `user_sets` exist.

- [ ] **Step 2: `GET /health` pings DB** — 503 when DB is down. Test with TestClient + Postgres fixture. Do not use SQLite.

`data_embeddings` is owned by Alembic; LlamaIndex writes through `OverdoneVectorStore` and must not create a second schema.

### Task B2: Baseline replace/read + text import

**Files:**
- Create: `backend/src/overdone/schemas/api.py`, `backend/src/overdone/services/baseline.py`, `backend/src/overdone/api/routers/baseline.py`, `backend/tests/test_baseline_api.py`, `data/sample_baseline.json`
- Modify: `backend/src/overdone/main.py`

**Interfaces:**
- Produces:

```python
async def replace_baseline(session: AsyncSession, payload: BaselineImport) -> Baseline: ...
async def replace_baseline_from_text(session: AsyncSession, text: str) -> Baseline: ...
async def get_baseline(session: AsyncSession) -> Baseline: ...
```

`PUT /api/v1/baseline` body = technical spec §5.2. Replace is wipe+insert in one transaction. Text path: parse JSON if the blob is JSON, else a date-line / `NxN @ weight` heuristic sufficient for tests.

- [ ] TestClient against Postgres:

```python
def test_put_sample_baseline_round_trips_session_notes():
    ...

def test_second_put_replaces_rather_than_appends():
    ...

def test_get_empty_baseline_is_empty_lists():
    ...
```

Verify: `cd backend && pytest tests/test_baseline_api.py -v`

### Task B3: Baseline panel in the UI

**Files:**
- Create: `frontend/src/components/BaselinePanel.tsx`
- Modify: `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts`, `page.tsx`

**Interfaces:** `putBaseline`, `putBaselineText`, `getBaseline`. Show session count, benchmark count, last error. No prompt box yet.

Verify in the browser: import sample JSON, refresh, counts hold.

---

# Slice C — Traffic lights (stub resolve, no RAG)

**Demo:** Load sample baseline, submit *“I want to add 20 lbs to my bench press tomorrow”* (name must match the log or a built-in alias). See overall light, gauges, 2–3 sentence narrative. Unknown lift and mixed units halt. Fatigue and substitution banners work. Re-submit replaces the verdict (no chat transcript).

**Slice DoD** — product matrix except qualitative *retrieval* and fuzzy catalog match:

- [ ] Single-session, multi-movement, macro via `POST /api/v1/evaluate`
- [ ] Itemized lights + overall
- [ ] Extreme +500 lb uses the same scorer (Red)
- [ ] Cold-start halt when the name is not in the baseline
- [ ] Ambiguous units halt
- [ ] In-prompt fatigue banner; scope disclaimer; evaluate does not insert sessions

### Task C1: Units + scoring + narrative (pure, no DB)

**Files:**
- Create: `backend/src/overdone/schemas/dto.py`, `backend/src/overdone/services/units.py`, `backend/src/overdone/services/scoring.py`, `backend/src/overdone/services/narrative.py`, `backend/tests/test_scoring.py`, `backend/tests/test_narrative.py`

**Interfaces:**

```python
def lb_to_kg(lb: float) -> float: ...
def kg_to_lb(kg: float) -> float: ...

def score_session(
    items: list[ProposedItem],
    last_by_exercise: dict[str, LogSet],
    enrichment: dict[str, ExerciseEnrichment],
) -> tuple[TrafficLight, list[ItemVerdict], FactorScores]: ...

def score_macro(
    *,
    current_kg: float,
    target_kg: float,
    weeks: int,
    weekly_velocity_kg: float,
    working: LogSet,
    enrichment: ExerciseEnrichment,
) -> ItemVerdict: ...

def session_narrative(overall: TrafficLight, items: list[ItemVerdict], factors: FactorScores) -> str: ...
def macro_narrative(verdict: ItemVerdict, weeks: int) -> str: ...
def scope_disclaimer() -> WarningFlag: ...
```

Copy DTOs from technical spec §5.1. Default enrichment in tests is a literal `ExerciseEnrichment` (no catalog).

- [ ] Failing tests from the product matrix (literals, not recomputed):

```python
def test_plus_20lb_bench_volume_jump_is_yellow_band():
    # last 185lb × 5 × 4; proposed 205lb × 5 × 4 → volume_jump_pct ≈ 10.8
    ...

def test_plus_500lb_bench_is_red_with_extreme_volume_jump():
    ...

def test_session_overall_worse_than_items_when_cns_stacks():
    ...

def test_macro_225_in_4_weeks_with_zero_velocity_is_red():
    ...

def test_qualitative_notes_do_not_change_volume_jump():
    ...
```

Use kg in the scorer. Convert in tests via `lb_to_kg`. Assert lights and `volume_jump_pct` rounded to 1 decimal.

- [ ] Implement formulas from technical spec §9.
- [ ] Narrative: 2–3 sentences; substitution string exact from the spec.

Verify: `cd backend && pytest tests/test_scoring.py tests/test_narrative.py -v`

### Task C2: Heuristic extractor

**Files:**
- Create: `backend/src/overdone/services/extract.py`, `backend/tests/test_extract.py`

**Interfaces:** `async def extract_prompt(text: str, *, llm_client: object | None = None) -> ExtractedPrompt`

Tests pass `llm_client=None` for the heuristic matrix; fakes cover timeout/validation fallback and unexpected errors. Mixed-unit halt is **not** the extractor’s job; omitted unit → `unit=None`.

Assert the product-spec prompt set: +20 lb single item; three-item session; 225 squat / `weeks=4`; fatigue copied; substitution flag; `"Add 200 to Bench"` has `unit=None`.

Optional Pydantic AI wrap when `OLLAMA_BASE_URL` is set; failures fall back to heuristic. No network in tests.

Verify: `cd backend && pytest tests/test_extract.py -v`

### Task C3: Stub resolve + evaluate HTTP

**Files:**
- Create: `backend/src/overdone/services/resolve.py` (`resolve_from_baseline` only), `backend/src/overdone/services/evaluate.py`, `backend/src/overdone/api/routers/evaluate.py`, `backend/tests/test_evaluate_api.py`
- Modify: `main.py`

**Interfaces:** `async def evaluate_prompt(session, prompt: str) -> EvaluationResult`

Order: extract → unit halt if mixed stored units and `unit is None` → **stub resolve** (casefold match to baseline names; built-in aliases like `db bench` / `bench press` → the baseline row’s name) → missing history halt → last-baseline lookup → score with **default enrichment constants** → fatigue/scope warnings → narrative.

`retrieve_context` is a no-op that returns `[]` in this slice.

`POST /api/v1/evaluate` always 200 with `halted` or verdict. Empty prompt 422.

| Prompt | Expect |
| :--- | :--- |
| +20 lb bench (alias or exact log name) | light + gauges, not halted |
| Multi-movement | `len(items) == 3`, overall + per-item |
| 225 squat next month | macro light + narrative |
| OHP with no history | `halted.reason == missing_exercise` |
| Mixed units + `"Add 200 to Bench"` | `ambiguous_units` |
| Slept 4 hours | `in_prompt_fatigue` |
| “…or tell me what to do instead” | disclaimer, still scored |
| +500 lb | red, extreme `volume_jump_pct` |
| Same prompt twice | identical JSON; session count unchanged |
| Shoulder tightness in log | **no** qualitative banner yet (Slice D) |

Verify: `cd backend && pytest tests/test_evaluate_api.py -v`

### Task C4: Prompt + verdict UI

**Files:**
- Create: `frontend/src/components/PromptPanel.tsx`, `frontend/src/components/VerdictPanel.tsx`
- Modify: `api.ts`, `types.ts`, `page.tsx`

One prompt field, Evaluate, replace-in-place verdict. Halt copy vs lights/gauges/banners. CSS bars only.

Verify in the browser: happy path, unknown lift, fatigue, no transcript on second submit. Also ~390px width.

---

# Slice D — Catalog + RAG

**Demo:** Seed mini (then full) catalog. Prompt uses a nickname not stored verbatim. Shoulder tightness from the log appears as a banner. Gauges use catalog enrichment, not only defaults.

**Slice DoD**

- [ ] Idempotent catalog seed; 384-d embeddings
- [ ] Similarity ≥ 0.78 binds `exercise_id`; below → missing exercise
- [ ] Note retrieve does not change scores
- [ ] Evaluate tests for qualitative_note pass
- [ ] UI shows the note banner

### Task D1: Catalog seed, enrichment, embeddings

**Files:**
- Create: `backend/src/overdone/ingest/catalog.py`, `data/enrichment_rules.json`, `backend/tests/test_catalog_ingest.py`, `backend/tests/fixtures/exercises_mini.json` (bench, incline press, pushdown, squat, OHP)
- Modify: optional CLI `python -m overdone.ingest.catalog`

**Interfaces:** `async def seed_catalog(session, exercises: list[dict]) -> int` — upsert `source_id`, enrichment, LlamaIndex `kind=exercise`. Re-run must not grow chunk count.

Pin MiniLM. Tests use the mini fixture only.

Verify: `cd backend && pytest tests/test_catalog_ingest.py -v`

### Task D2: Embedding resolve + retrieve

**Files:**
- Modify: `backend/src/overdone/services/resolve.py`, create `backend/src/overdone/services/retrieve.py`, `backend/tests/test_resolve.py`, `backend/tests/test_retrieve.py`
- Modify: `replace_baseline` to rebuild `kind=session_note` chunks

**Interfaces:**

```python
async def resolve_exercise_name(session, name: str) -> str | None:
    """exercises.id or None if similarity < 0.78."""

async def retrieve_context(session, *, exercise_ids: list[str], prompt: str) -> RetrieveResult:
    """kind=exercise citations + kind=session_note. Includes source_id."""
```

Stub resolve remains a first pass; embedding resolve runs if the stub misses.

Tests: exact name; alias; unknown string `None`; retrieve `source_id`; “shoulder felt tight” for a bench prompt.

Verify: `cd backend && pytest tests/test_resolve.py tests/test_retrieve.py -v`

### Task D3: Wire evaluate + UI banner

**Files:**
- Modify: `evaluate.py` (call retrieve; qualitative warnings), `test_evaluate_api.py` (note banner row), `VerdictPanel.tsx`

Verify: evaluate tests including qualitative_note; browser shows `Note from …`.

---

# Slice E — MCP + full DoD

**Demo:** In-process MCP client (and `/mcp`) returns the same `EvaluationResult` as HTTP. Fresh `docker compose up` migrates and seeds an empty DB.

**Slice DoD:** product-spec Definition of Done checklist (all boxes).

### Task E1: FastMCP mount

**Files:**
- Create: `backend/src/overdone/mcp/server.py`, `backend/tests/test_mcp.py`
- Modify: `main.py` — Streamable HTTP at `/mcp`

Tools: `get_baseline_status`, `replace_baseline_json`, `replace_baseline_text`, `evaluate_prompt` — same services as routers.

```python
async def test_evaluate_prompt_tool_returns_light():
    ...
```

Verify: `cd backend && pytest tests/test_mcp.py -v`

### Task E2: Seed-on-boot + product DoD

**Files:**
- Modify: `compose.yaml` (api waits on db healthy; web on api; optional `profiles: [llm]` ollama), API lifespan migrate + seed catalog if empty. Short `README.md` run instructions only if needed.

Verify in order (evidence = command output):

```bash
docker compose up -d --build --wait
curl -sf http://localhost:8000/health
cd backend && ruff check . && ruff format --check . && pytest -v
cd frontend && npx tsc --noEmit
```

Product DoD:

1. Postgres + pgvector healthy.
2. Catalog seeded and enriched.
3. Sample JSON + a plain-text log both populate baseline.
4. MCP `evaluate_prompt` and HTTP agree on a single-session and a macro prompt.
5. Multi-exercise itemization present.
6. Narrative + gauges in UI.
7. Unknown lift and mixed-unit halt copy in UI.
8. Note + fatigue banners.
9. Substitution disclaimer, no generated alternative workout.
10. +500 lb → Red with large volume %.
11. Re-evaluate does not add sessions (`GET /api/v1/baseline` session count stable).

---

## Suggested commit points (when you ask to commit)

One commit per finished slice is enough; split further only if a slice is large:

1. `chore: bootstrap compose, API health, and UI status`
2. `feat: persist a replaceable training baseline`
3. `feat: evaluate prompts with traffic lights in the scratchpad`
4. `feat: resolve exercises and surface log notes via RAG`
5. `feat: expose the same evaluation over MCP`

## Execution notes

- Slice C is the first *product* increment. A and B exist so C is not a 20-file bang.
- Do not implement substitution generation, auth, or a second vector store if a test is red.
- If Ollama is missing, extraction stays heuristic; DoD must still pass on the product-spec prompt set.
- After a slice, stop and demo before starting the next.
