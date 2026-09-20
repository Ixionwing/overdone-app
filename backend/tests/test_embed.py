from __future__ import annotations

import pytest

from overdone.ingest.embed import embed_query, embed_texts, recording_embeddings


def test_embed_query_unknown_text_is_missing_from_fixture() -> None:
    if recording_embeddings():
        pytest.skip("recording mode embeds missing texts instead of raising")
    with pytest.raises(KeyError, match="embedding fixture missing"):
        embed_query("definitely-not-a-captured-embedding-string-xyz")


def test_embed_query_fixture_vector_is_384d() -> None:
    vector = embed_query("Barbell Bench Press - Medium Grip")
    assert len(vector) == 384
    assert embed_texts([]) == []
