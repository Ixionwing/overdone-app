# Overdone — Technical Specification (POC)

This document turns `product-spec.md` into implementable contracts: services, schemas, formulas, APIs, and test seams. Product behavior in `product-spec.md` wins when this file and the product spec disagree. Numbers below are **POC defaults** so scoring is deterministic and testable; they are not clinical guidance.

## 1. Decisions (confirmed 2026-09-20)

1. **Extraction model.** Required OpenAI-compatible local endpoint (`OLLAMA_BASE_URL`, model `llama3.2`, timeout 30s). No heuristic fallback. Scoring, traffic lights, and narratives never call a model.
2. **Frontend.** Next.js (App Router) + TypeScript over HTTP to FastAPI. MCP is for agents, not the browser.
3. **Identity.** Single local user, no auth. Baseline tables are global to the compose stack.

Implementation is sliced in `docs/implementation-plan.md`. Each slice is a demoable increment.

## 2. Goal and non-goals

**Goal.** Local full-stack scratchpad: ingest a static training baseline, parse a natural-language proposed change, score it with fixed rules, retrieve supporting biomechanics/log context, and render Green / Yellow / Red plus gauges. Same evaluation is available over HTTP and MCP.

**In scope**

- Baseline paste / JSON file import (persisted).
- Single-session (one or many movements) and macro-goal evaluation.
- Deterministic traffic lights, itemized per-exercise lights, template narratives, gauges.
- Guards: missing exercise, mixed-unit ambiguity, diagnostic-only scope.
- Qualitative log notes and in-prompt fatigue as **banners only**.
- Postgres 16 + pgvector, local embeddings, FastMCP tools mounted on FastAPI.
- Docker Compose for Postgres, API, and web.

**Out of scope (POC)**

- Accounts, auth, multi-tenant history.
- Calendar writes, program generation, substitutions, coaching chat memory.
- Kubernetes, cloud vector DBs, paid embedding APIs.
- Mutating logs or storing prompt/verdict history.
- Clinical accuracy of load models; formulas are explicit POC heuristics.

## 3. Runtime architecture

```
Browser (Next.js) --HTTP JSON--> FastAPI
Cursor / agents  --MCP (mounted)--> same FastAPI process
                                      |
                                      +--> Pydantic AI extractor (required LLM)
                                      +--> deterministic scoring
                                      +--> SQLAlchemy (logs, 1RMs, enrichment)
                                      +--> LlamaIndex ingest (exercise catalog -> pgvector)
                                      +--> SQL/pgvector retrieve_context (catalog + notes)
                                      |
PostgreSQL 16 + pgvector <------------+
```

**Process split**

| Service | Image / runtime | Role |
| :--- | :--- | :--- |
| `db` | `pgvector/pgvector:pg16` | Relational logs + vectors |
| `api` | Python 3.12, FastAPI + FastMCP | HTTP + MCP, ingest, evaluate |
| `web` | Node, Next.js | Scratchpad UI |
| `ollama` (optional profile) | Ollama | Chat model for extraction only |

One API process. FastMCP is mounted on FastAPI (stdio is not the default compose transport; Streamable HTTP on the same port as the API, e.g. `/mcp`).

**Stateless rule.** `POST /evaluate` and the MCP `evaluate_prompt` tool are read-only against user history. The only user writes are baseline import/replace. Evaluations live in the response only.

## 4. Repository layout

```
overdone-app/
  product-spec.md
  docs/technical-spec.md
  docs/implementation-plan.md
  compose.yaml
  .env.example
  backend/
    Dockerfile
    pyproject.toml
    alembic.ini
    alembic/
    src/overdone/
      main.py                 # FastAPI app, MCP mount, lifespan
      api/deps.py
      api/routers/health.py
      api/routers/baseline.py
      api/routers/evaluate.py
      models/                 # SQLAlchemy
      schemas/                # Pydantic API + domain DTOs
      services/extract.py
      services/baseline.py
      services/scoring.py
      services/narrative.py
      services/retrieve.py
      services/evaluate.py    # orchestrator
      ingest/catalog.py       # LlamaIndex seed
      mcp/server.py
    tests/
  frontend/
    Dockerfile
    package.json
    src/app/page.tsx
    src/lib/api.ts
    src/components/...
  data/
    free-exercise-db/         # vendored or downloaded dist/exercises.json
    enrichment_rules.json     # axial / CNS / joint overlays
    sample_baseline.json
```

Python lives in `backend/` (`overdone` package). UI lives in `frontend/`. No second ORM. No Prisma.

**Tooling (bootstrapping)**

- Backend: Ruff (`I`, `UP` + format), Pyright `standard`, pytest.
- Frontend: ESLint recommended + `typescript-eslint` + React Hooks + Prettier; `tsc --noEmit` strict.
- Docker: `# syntax=docker/dockerfile:1`, non-root `USER`, pin tags, `.dockerignore`.

## 5. Domain model

Canonical mass unit in storage and math: **kilograms**. Display may use `lb` or `kg`. `1 lb = 0.45359237 kg`.

### 5.1 Pydantic DTOs (orchestrator contract)

```python
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field


class TrafficLight(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class PromptKind(str, Enum):
    single_session = "single_session"
    macro_goal = "macro_goal"


class HaltReason(str, Enum):
    missing_baseline = "missing_baseline"
    missing_exercise = "missing_exercise"
    ambiguous_units = "ambiguous_units"
    extract_failed = "extract_failed"


class Unit(str, Enum):
    lb = "lb"
    kg = "kg"


class LogSet(BaseModel):
    exercise_id: str | None = None
    exercise_name: str
    weight_kg: float
    reps: int
    sets: int = 1


class SessionLog(BaseModel):
    logged_on: date
    notes: str | None = None
    sets: list[LogSet]


class Benchmark(BaseModel):
    exercise_id: str | None = None
    exercise_name: str
    one_rm_kg: float


class Baseline(BaseModel):
    preferred_unit: Unit = Unit.lb
    benchmarks: list[Benchmark] = Field(default_factory=list)
    sessions: list[SessionLog] = Field(default_factory=list)


class ProposedItem(BaseModel):
    exercise_name: str
    exercise_id: str | None = None
    weight_kg: float | None = None
    delta_kg: float | None = None
    reps: int | None = None
    sets: int | None = None
    extra_sets: int | None = None


class ExtractedPrompt(BaseModel):
    kind: PromptKind
    items: list[ProposedItem]
    target_date: date | None = None
    weeks: int | None = None
    target_weight_kg: float | None = None
    target_exercise_name: str | None = None
    declared_fatigue: str | None = None
    asks_substitution: bool = False
    unit: Unit | None = None
    raw_text: str


class FactorScores(BaseModel):
    volume_jump_pct: float
    axial_compression: float
    cns_index: float
    joint_vectors: dict[str, float]


class ItemVerdict(BaseModel):
    exercise_id: str
    exercise_name: str
    light: TrafficLight
    factors: FactorScores
    narrative: str
    catalog_source_id: str | None = None


class WarningFlag(BaseModel):
    kind: str  # qualitative_note | in_prompt_fatigue | scope_disclaimer
    message: str
    source_id: str | None = None


class Halt(BaseModel):
    reason: HaltReason
    message: str
    exercise_name: str | None = None


class EvaluationResult(BaseModel):
    halted: Halt | None = None
    overall_light: TrafficLight | None = None
    items: list[ItemVerdict] = Field(default_factory=list)
    session_factors: FactorScores | None = None
    narrative: str | None = None
    warnings: list[WarningFlag] = Field(default_factory=list)
```

### 5.2 Baseline JSON import schema

`data/sample_baseline.json` is the fixture. Plain-text import is parsed into this same shape.

```json
{
  "preferred_unit": "lb",
  "benchmarks": [
    { "exercise": "Barbell Bench Press - Medium Grip", "one_rm": 225, "unit": "lb" }
  ],
  "sessions": [
    {
      "date": "2026-09-13",
      "notes": "Right shoulder felt tight on set 3",
      "sets": [
        {
          "exercise": "Barbell Bench Press - Medium Grip",
          "weight": 185,
          "unit": "lb",
          "reps": 5,
          "sets": 4
        }
      ]
    }
  ]
}
```

Unknown keys are rejected (Pydantic extra=forbid). Missing `unit` on a row inherits `preferred_unit`. Import **replaces** the current baseline (scratchpad, one active history). On replace, each set/benchmark name is resolved against the catalog; bound rows store `exercises.id` and GET echoes it as optional `exercise_id`. Client-supplied `exercise_id` is ignored and re-resolved from `exercise`. Unmatched names stay `null`.

### 5.3 SQLAlchemy tables

Naming convention on `MetaData`. `lazy="raise"` on relationships. Alembic owns `CREATE EXTENSION IF NOT EXISTS vector`.

| Table | Purpose |
| :--- | :--- |
| `exercises` | Catalog row from free-exercise-db (`source_id`, `name`, muscles, equipment, …) |
| `exercise_enrichment` | POC axial / CNS / joint factors keyed by `exercises.id` |
| `exercise_aliases` | Extra names for matching (`DB Bench` → catalog id) |
| `data_embeddings` | Alembic table written by LlamaIndex (`OverdoneVectorStore`, 384-d `vector`) |
| `user_benchmarks` | Active 1RMs |
| `user_sessions` | Logged sessions (`logged_on`, `notes`) |
| `user_sets` | Sets belonging to a session |

No `evaluations` or `messages` tables.

`data_embeddings` stores two namespaces (LlamaIndex metadata filter):

- `kind=exercise` — name + muscles + instructions + enrichment blurb.
- `kind=session_note` — non-empty session notes, with `session_id` and date. Rebuilt on baseline replace.

## 6. Catalog seed and enrichment

Source: [yuhonas/free-exercise-db](https://github.com/yuhonas/free-exercise-db) `dist/exercises.json`.

Seed is idempotent: upsert on `source_id`. Re-ingest must not duplicate embedding chunks (delete+rewrite per `source_id` or content hash).

**Embeddings.** `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, local, no API key. This is required by the product spec (the ingest skill’s OpenAI default does not apply).

`data/enrichment_rules.json` overlays factors the upstream DB does not have. Lookup order: exact `source_id` → primary-muscle / mechanic rules → defaults.

| Field | Range | Default rule |
| :--- | :--- | :--- |
| `axial_factor` | 0.0–1.0 | 0.9 squat/deadlift/good-morning ids; 0.6 hinge / `lower back` primary; 0.15 else |
| `cns_factor` | 0.0–1.0 | 0.85 `mechanic=compound`; 0.5 olympic/strongman category; 0.25 isolation |
| `joints` | map joint → 0.0–1.0 | shoulder: chest/shoulders/triceps pressing; knee: quads/glutes squat-lunge; spine: axial_factor |

POC joint keys: `shoulder`, `knee`, `spine`, `elbow`. Missing joint = 0.

## 7. Exercise resolution

Pipeline: alias table → casefold exact name → embedding nearest neighbor (`kind=exercise`).

- Cosine similarity **≥ 0.78** → bind `exercise_id`.
- Below threshold → `HaltReason.missing_exercise` (same as “not in user history” after a successful catalog match with no baseline row).

Cold start: catalog match **and** no sets/1RM for that `exercise_id` → halt and ask for 1RM or working weight. Do not score.

## 8. Prompt extraction

`services/extract.py` returns `ExtractedPrompt`.

1. Call the Pydantic AI agent with `output_type=ExtractedPrompt` (minus `exercise_id`; resolver fills ids later).
2. On missing client, timeout, connection/validation/`AgentRunError`, empty session items, or a macro missing target → `HaltReason.extract_failed`.
3. Tests never call the network; inject a fake extract client.

**Unit guard.** If baseline sessions/benchmarks contain **both** `lb` and `kg` (after normalizing stored kg, keep original unit on the row) **and** the prompt has a magnitude with no unit → halt `ambiguous_units`. If baseline is single-unit, inherit that unit.

**Kind.**

- Macro if a future horizon + target load appears (`225 by next month`).
- Otherwise single-session (one or more `ProposedItem`s).

**Fatigue.** Copy the user’s clause into `declared_fatigue`; do not parse sleep hours into a score.

**Substitution.** `asks_substitution=true` if the text requests alternatives / “what should I do instead”.

## 9. Deterministic scoring

All lights use `max()` of contributing factors. Extreme prompts use this same path (no special case).

### 9.1 Last baseline for an exercise

Prefer the most recent session that contains the exercise. Working prescription:

- `last_weight_kg` = heaviest set weight that session
- `last_sets`, `last_reps` = matching set’s sets/reps (if several rows, use the heaviest)
- `last_tonnage_kg` = Σ `weight_kg * reps * sets` for that exercise that session

If no session but a 1RM exists: synthesize `last_weight_kg = 0.80 * one_rm_kg`, `last_sets=3`, `last_reps=5` (POC stand-in for a working set). Tonnage from that.

### 9.2 Proposed session item

Fill gaps from last baseline: omitted sets/reps/weight stay at last values; `delta_kg` adds to last weight; `extra_sets` adds to last sets.

```
proposed_tonnage = proposed_weight_kg * proposed_reps * proposed_sets
volume_jump_pct = (proposed_tonnage - last_tonnage) / last_tonnage * 100
```

If `last_tonnage == 0`, treat `volume_jump_pct` as `1000` (forces Red).

```
axial_compression = proposed_tonnage * axial_factor
cns_index = proposed_tonnage * cns_factor
joint_vectors[j] = proposed_tonnage * joints[j]
```

Session aggregates: **sum** tonnage-derived scores across items. Session volume jump uses total proposed vs total last tonnage for those exercises.

### 9.3 Traffic light thresholds (POC)

| Factor | Green | Yellow | Red |
| :--- | ---: | ---: | ---: |
| Volume jump % | `< 10` | `10–20` | `> 20` |
| Axial vs last axial % jump | `< 10` | `10–20` | `> 20` |
| CNS vs last CNS % jump | `< 15` | `15–30` | `> 30` |
| Any joint vs last joint % jump | `< 15` | `15–30` | `> 30` |

Item light = worst of its factors. Session overall = worse of (worst item light, session-aggregate factors). That is how “each jump is modest but the session stacks” goes Yellow/Red.

### 9.4 Macro feasibility

Inputs: target weight, horizon weeks (default `4` if “next month”), current `last_weight_kg`.

```
required_weekly_kg = (target_weight_kg - current_kg) / weeks
```

Historical velocity: for that exercise, sort sessions by date, take last **≤ 8** sessions with the lift, compute mean weekly weight change (heaviest set).

Rate light:

| Condition | Light |
| :--- | :--- |
| Fewer than 2 dated sessions and `required_weekly_kg ≤ 1.5` | Green (no history is not “overdone”) |
| Fewer than 2 dated sessions and `required_weekly_kg > 1.5` | Red |
| `required_weekly_kg ≤ 1.0 * velocity` | Green |
| `≤ 1.5 * velocity` | Yellow |
| else | Red |

Macro gauges use the named target prescription when sets/reps were extracted; otherwise last working sets/reps at the target weight (same formulas as 9.2). Overall macro light is the worse of the rate light and that implied-prescription light. Narrative states feasibility, not a session plan.

### 9.5 Narrative (no LLM)

`services/narrative.py` fills 2–3 sentences from `ItemVerdict` / session aggregates: exercise names, `%` jumps, light, and a one-line physiological gloss from the dominant factor (`volume`, `axial`, `cns`, `joint:shoulder`, …). Tests assert substrings, not model prose.

Scope disclaimer warning when `asks_substitution`:

`Diagnostic evaluation complete; exercise substitution is outside scope.`

## 10. RAG (query time)

LlamaIndex **writes** the index. `retrieve_context` **reads** the same `data_embeddings` rows over SQL/pgvector. Pydantic AI is the required extractor when `OLLAMA_BASE_URL` is set, not the retrieve agent. MCP tools must not re-implement ingest.

Retrieve (k=4) for:

1. Bound exercises (biomechanics chunk) → `ItemVerdict.catalog_source_id` on gauges/help text.
2. Session notes that are qualitative **and** (keyword overlap with bound joints/muscles **or** semantic similarity ≥ 0.35). **Do not** change scores.

Note banner format: `Note from {relative day}: '{quote}'`.

In-prompt fatigue banner: `User declared: '{declared_fatigue}'`.

## 11. HTTP API

Prefix `/api/v1`. Pydantic request/response models. `HTTPException` for 4xx. `Depends()` for `AsyncSession`.

| Method | Path | Behavior |
| :--- | :--- | :--- |
| `GET` | `/health` | `{ "status": "ok" }`; 503 if DB ping fails |
| `GET` | `/api/v1/baseline` | Current baseline DTO or empty |
| `PUT` | `/api/v1/baseline` | Replace from JSON body |
| `POST` | `/api/v1/baseline/text` | `{ "text": "..." }` → extract → replace |
| `POST` | `/api/v1/evaluate` | `{ "prompt": "..." }` → `EvaluationResult` |

Evaluate always 200 with either `halted` or a full verdict (guards are domain results, not 400, so the UI can render the ask-for-1RM / ask-for-unit copy). Malformed JSON is 422. Empty prompt is 422.

## 12. MCP tools

In-process FastMCP, same functions as the routers.

| Tool | Args | Returns |
| :--- | :--- | :--- |
| `get_baseline_status` | — | counts of sessions, benchmarks, missing-catalog warnings |
| `replace_baseline_json` | JSON string | status |
| `replace_baseline_text` | text | status |
| `evaluate_prompt` | prompt | `EvaluationResult` JSON |

Tools call services. They do not ingest the exercise catalog.

## 13. Frontend (scratchpad)

Single page, two regions, no routing beyond `/`.

1. **Baseline box** — textarea, JSON file input, replace/save, confirmation of session/benchmark counts, last import error.
2. **Prompt box** — one shot evaluate. No chat transcript. Submitting again does not show the previous prompt unless the user left it in the input.
3. **Verdict** — overall light, per-item lights, 2–3 sentence narrative, four gauges (volume %, axial, CNS, joints), warning banners. Halt states show only the clarification prompt.

Gauges are CSS progress bars bound to the numeric fields; no chart library in the POC.

## 14. Compose and config

`compose.yaml`: `db`, `api`, `web`. Healthcheck on Postgres (`pg_isready`) and API (`GET /health`). API waits on `db` healthy. Web `NEXT_PUBLIC_API_URL` points at the API service.

`.env.example` (no secrets required for the default path):

```
POSTGRES_USER=overdone
POSTGRES_PASSWORD=overdone
POSTGRES_DB=overdone
DATABASE_URL=postgresql+asyncpg://overdone:overdone@db:5432/overdone
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OLLAMA_BASE_URL=http://ollama:11434/v1
OLLAMA_MODEL=llama3.2
```

Local `.env` is gitignored. Do not read or commit `.env.production`.

## 15. Test seams

Confirm these public seams; tests do not reach into private helpers or the live LLM.

| Seam | How |
| :--- | :--- |
| Scoring + lights | Pure functions, fixture logs, literal expected % and lights |
| Extractor | Injected fake client; fail-closed `extract_failed` |
| Baseline replace | API `TestClient` + Postgres testcontainer / compose |
| Evaluate orchestrator | Fake retrieve + real scoring; halt paths |
| RAG retrieve | Fixture embeddings, assert `source_id`s |
| MCP | In-process FastMCP client |
| Catalog seed | Idempotent upsert, row counts |
| Frontend | Component/API-client tests for halt vs verdict rendering; no network |

Do not use SQLite as a stand-in for Postgres/pgvector.

## 16. Product-spec traceability

| Product requirement | Spec section |
| :--- | :--- |
| Plain text / JSON baseline, mandatory history | 5.2, 11, 13 |
| Missing exercise / 1RM cold start | 7, 8 |
| Single-session, multi-exercise, macro | 8, 9 |
| Traffic lights + itemization | 9.3, 5.1 |
| Hybrid rationale + gauges | 9.5, 13 |
| Qualitative notes, fatigue flags | 10 |
| Static last baseline (ignore time gaps) | 9.1 |
| Unit enforcement | 8 |
| No substitutions | 8, 9.5 |
| Extreme prompts, standard math | 9 |
| Stateless prompts | 3, 5.3 |
| FastMCP, optional Pydantic AI extract, pgvector, MiniLM, free-exercise-db | 3, 6, 8, 10, 12 |
| DoD container / seed / tools / UI | 14, 6, 12, 13 |
