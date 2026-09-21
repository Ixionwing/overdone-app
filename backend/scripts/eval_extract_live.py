"""Optional live extract eval against Ollama. Not invoked by pytest.

OVERDONE_LIVE_EXTRACT=1 uv run python scripts/eval_extract_live.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from overdone.config import Settings
from overdone.schemas.extract_draft import ExtractDraft
from overdone.services.extract_llm import extract_client_from_settings

GOLD = (
    Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "golden_extract.json"
)


def _amount_ok(expected: float | None, got: float | None) -> bool:
    if expected is None and got is None:
        return True
    if expected is None or got is None:
        return False
    if expected == 0:
        return abs(got) < 1e-6
    return abs(got - expected) / abs(expected) <= 0.01


def _item_ok(expected: dict, got) -> bool:
    if expected.get("amount_kind") != (
        got.amount_kind.value if got.amount_kind else None
    ):
        return False
    if expected.get("amount_unit") != got.amount_unit:
        return False
    return _amount_ok(expected.get("amount"), got.amount)


def _row_ok(row: dict, draft: ExtractDraft) -> str | None:
    expected = row["draft"]
    if draft.kind != expected["kind"]:
        return "kind mismatch"
    gold_items = expected["items"]
    if len(draft.items) != len(gold_items):
        return "item count mismatch"
    for gold_item, got in zip(gold_items, draft.items, strict=True):
        if not _item_ok(gold_item, got):
            return "amount mismatch"
        name = got.name.casefold()
        token = gold_item["name"].casefold().split()[0]
        if token not in name and name.split()[0] not in gold_item["name"].casefold():
            return "name mismatch"
    return None


async def _run() -> int:
    if os.environ.get("OVERDONE_LIVE_EXTRACT") != "1":
        print("skip: set OVERDONE_LIVE_EXTRACT=1 to call Ollama")
        return 0
    client = extract_client_from_settings(Settings())
    if client is None:
        print("fail: OLLAMA_BASE_URL is not set")
        return 1
    rows = json.loads(GOLD.read_text())
    ok = 0
    for row in rows:
        prompt = row["prompt"]
        try:
            draft = await client.extract(prompt)
        except Exception as exc:  # noqa: BLE001 — live script reports any failure
            print(f"extract_failed\t{row['id']}\t{exc}")
            continue
        reason = _row_ok(row, draft)
        if reason is None:
            ok += 1
            print(f"ok\t{row['id']}")
        else:
            print(f"{reason}\t{row['id']}")
    print(f"{ok}/{len(rows)} ok")
    return 0 if ok == len(rows) else 2


def main() -> None:
    sys.exit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
