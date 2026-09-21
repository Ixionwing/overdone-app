from __future__ import annotations

import json
from pathlib import Path


def golden_extract_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "tests" / "fixtures" / "golden_extract.json"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("tests/fixtures/golden_extract.json not found")


def load_golden_extract() -> list[dict]:
    return json.loads(golden_extract_path().read_text())


def fewshot_examples() -> list[tuple[str, dict]]:
    return [
        (row["prompt"], row["draft"])
        for row in load_golden_extract()
        if row.get("fewshot")
    ]
