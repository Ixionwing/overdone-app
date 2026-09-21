"""One-shot: write tests/fixtures/mini_embeddings.json using MiniLM.

Run from backend/: uv run python tests/fixtures/build_mini_embeddings.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from overdone.ingest.embed import (
    embed_texts,
    load_embedding_fixture,
    save_embedding_fixture,
)
from overdone.ingest.enrichment import chunk_text, enrichment_for, load_rules

ROOT = Path(__file__).resolve()
MINI = ROOT.parent / "exercises_mini.json"
OUT = ROOT.parent / "mini_embeddings.json"
SAMPLE = ROOT.resolve().parents[3] / "data" / "sample_baseline.json"

QUERIES = [
    "Barbell Bench Press - Medium Grip",
    "Incline Dumbbell Press",
    "Cable Pushdown",
    "Barbell Squat",
    "Standing Military Press",
    "DB Bench",
    "DB Bench Press",
    "Bench",
    "Bench Press",
    "Incline DB Press",
    "Pushdowns",
    "Pushdown",
    "Squat",
    "OHP",
    "Overhead Press",
    "medium grip barbell bench",
    "zzzxnotanexercise999",
    "add 20 lbs to bench press",
    "Add 20 lbs to bench tomorrow",
    "Add 20 lbs to medium grip barbell bench tomorrow.",
    "I want to make my cable pushdown 3 sets of 10 reps, 45lbs each",
    "Add 20 lbs to Bench tomorrow, 3 sets of 8",
    "I want to add 20 lbs to my bench press tomorrow",
    "Tomorrow: +10 lbs Bench, +5 lbs Incline DB Press, +3 sets Pushdowns.",
    "Reach a 225 lb Squat by next month.",
    "4 sets of 185 lb Overhead Press tomorrow.",
    "Add 200 to Bench tomorrow.",
    "Slept 4 hours, but want to add 10 lbs to Bench tomorrow.",
    "Add 30 lbs to Bench tomorrow, or tell me what to do instead.",
    "Add 500 lbs to my Bench Press tomorrow.",
    "Add 20 lbs to Bench tomorrow.",
    "Right shoulder felt tight on set 3",
    "Left knee felt tight on set 3",
    "Shin splint pain after jogging",
    "only this session",
]


def main() -> None:
    exercises = json.loads(MINI.read_text())
    rules = load_rules()
    texts: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        if value and value not in seen:
            seen.add(value)
            texts.append(value)

    for item in exercises:
        factors = enrichment_for(item, rules)
        add(chunk_text(item, factors))
        add(str(item["name"]))
        for alias in (rules.get("aliases") or {}).get(item["id"], []):
            add(str(alias))
    if SAMPLE.exists():
        sample = json.loads(SAMPLE.read_text())
        for session in sample.get("sessions") or []:
            note = session.get("notes")
            if note:
                add(str(note))
    for query in QUERIES:
        add(query)

    load_embedding_fixture(OUT, record=True)
    asyncio.run(embed_texts(texts))
    from overdone.ingest import embed as embed_mod

    embed_mod._dirty = True
    save_embedding_fixture()
    print(f"wrote {len(texts)} vectors to {OUT}")


if __name__ == "__main__":
    main()
