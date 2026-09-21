# Cursor MCP workflow

Anyone who clones this repo can score a training increment from Cursor without building an in-app chat. Cursor is the outer agent; Overdone only extracts and scores.

Evaluations are still scratchpad: nothing is stored. Prefer the one-shot `log` argument so a demo does not stomp the UI baseline.

## 1. Start the stack

Postgres 16 + pgvector on `DATABASE_URL` (local default port **5433**), host Ollama on **11434**, API on **8000**, optional UI on **3000**.

From `backend/`:

```bash
uv sync
alembic upgrade head
uv run python -m overdone.ingest
OLLAMA_BASE_URL=http://127.0.0.1:11434/v1 OLLAMA_MODEL=llama3.2 \
  uv run uvicorn overdone.main:app --reload --port 8000
```

Compose instead: `docker compose up --build` (set `OLLAMA_BASE_URL` as in the README). Confirm `http://localhost:8000/health` and that `/mcp` is mounted.

Optional UI: `cd frontend && npm ci && npm run dev`.

## 2. Enable the project MCP server

This repo ships `.cursor/mcp.json` pointing at `http://127.0.0.1:8000/mcp` (`type: http`). After you open the folder in Cursor, enable **overdone** if the MCP panel asks. The rule `.cursor/rules/overdone-mcp.mdc` describes the loop for the agent.

If the tool list is empty, the API is down or Ollama is unset (evaluate will not mount).

## 3. Run the three dogfood threads

Attach `@data/sample_baseline.txt` (or paste it) and let the agent pass that text as `log`. Do not call `replace_baseline_text` unless you intend to change the left pane.

**What-if increments.** Same log, two `evaluate_prompt` calls:

- `I want to add 20 lbs to my bench press tomorrow`
- `I want to add 5 lbs to my bench press tomorrow`

Compare `overall_light` and `items[0].factors.volume_jump_pct`. The +20 should jump more than the +5. Sample week-2 Push A includes `notes: Right shoulder felt tight on set 3` — expect a `qualitative_note` warning. It must not flip the light by itself.

**Messy phrasing.** Ask the agent to rewrite something like “idk maybe jump the bench a bunch tomorrow if the shoulder is ok” into a concrete increment, then score **only** the rewrite. Use `extract` on the tool body to see what the model parsed (`items`, units, fatigue). If extract is empty or `halted.reason` is `extract_failed`, say so; do not guess a score.

**Halt vs light.** Try an exercise that is not in the sample log, or skip `log` with an empty database. You should get `halted` (`missing_exercise` / `missing_baseline`) with a next step, not a invented Green.

## 4. What not to add

No `evaluate_many`, no coach/CI gate, no persisted verdicts. `replace_baseline_*` is the UI import pane as a tool; the Cursor demo should not need it.

REST stays prompt-only (`POST /api/v1/evaluate`). The browser still scores against the imported singleton. MCP is allowed to pass `log` so a clone-and-run chat can stay one-shot.
