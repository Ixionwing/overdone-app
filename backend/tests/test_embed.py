from __future__ import annotations

import asyncio
import time

import pytest

from overdone.ingest.embed import embed_query, embed_texts, recording_embeddings


def test_embed_query_unknown_text_is_missing_from_fixture() -> None:
    if recording_embeddings():
        pytest.skip("recording mode embeds missing texts instead of raising")
    with pytest.raises(KeyError, match="embedding fixture missing"):
        asyncio.run(embed_query("definitely-not-a-captured-embedding-string-xyz"))


def test_embed_query_fixture_vector_is_384d() -> None:
    vector = asyncio.run(embed_query("Barbell Bench Press - Medium Grip"))
    assert len(vector) == 384
    assert asyncio.run(embed_texts([])) == []


def test_model_encode_does_not_block_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OVERDONE_REAL_EMBEDDINGS", "1")

    def fake_model_embed(texts: list[str], model_name: str | None) -> list[list[float]]:
        time.sleep(0.25)
        return [[0.0] * 384 for _ in texts]

    monkeypatch.setattr("overdone.ingest.embed._model_embed", fake_model_embed)

    async def run() -> int:
        ticks = 0

        async def ticker() -> None:
            nonlocal ticks
            while True:
                await asyncio.sleep(0.02)
                ticks += 1

        task = asyncio.create_task(ticker())
        try:
            vector = await embed_query("loop-probe")
            assert len(vector) == 384
        finally:
            task.cancel()
        return ticks

    assert asyncio.run(run()) >= 5
