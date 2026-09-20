from __future__ import annotations

import asyncio
import json
import os
from functools import lru_cache
from pathlib import Path

from overdone.config import settings

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_fixture: dict[str, list[float]] = {}
_fixture_path: Path | None = None
_recording = False
_dirty = False


def _model_name(explicit: str | None) -> str:
    name = explicit or settings.embedding_model
    if not name:
        raise RuntimeError("embedding_model is not configured")
    return name


def _check_dim(vectors: list[list[float]]) -> None:
    expected = settings.embedding_dimensions
    for vector in vectors:
        if len(vector) != expected:
            raise ValueError(f"embedding dim {len(vector)} does not match {expected}")


def use_real_embeddings() -> bool:
    return os.environ.get("OVERDONE_REAL_EMBEDDINGS") == "1"


def recording_embeddings() -> bool:
    return os.environ.get("OVERDONE_RECORD_EMBEDDINGS") == "1" or _recording


def load_embedding_fixture(path: Path, *, record: bool = False) -> None:
    global _fixture, _fixture_path, _recording, _dirty
    _fixture_path = path
    _recording = record
    _dirty = False
    if path.exists():
        raw = json.loads(path.read_text())
        _fixture = {
            str(key): [float(item) for item in value] for key, value in raw.items()
        }
    elif record:
        _fixture = {}
    else:
        raise FileNotFoundError(f"embedding fixture missing: {path}")


def save_embedding_fixture() -> None:
    if _fixture_path is None or not _dirty:
        return
    _fixture_path.write_text(json.dumps(_fixture, separators=(",", ":")))


def clear_embedding_fixture() -> None:
    global _fixture, _fixture_path, _recording, _dirty
    _fixture = {}
    _fixture_path = None
    _recording = False
    _dirty = False


@lru_cache(maxsize=4)
def get_embed_model(model_name: str = DEFAULT_EMBEDDING_MODEL):
    name = _model_name(model_name)
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(model_name=name)


def _model_embed(texts: list[str], model_name: str | None) -> list[list[float]]:
    model = get_embed_model(_model_name(model_name))
    vectors = [list(vec) for vec in model.get_text_embedding_batch(texts)]
    _check_dim(vectors)
    return vectors


async def _lookup_or_embed(
    texts: list[str], model_name: str | None
) -> list[list[float]]:
    global _dirty
    if use_real_embeddings() and not recording_embeddings():
        return await asyncio.to_thread(_model_embed, texts, model_name)
    if _fixture_path is None and not _recording:
        return await asyncio.to_thread(_model_embed, texts, model_name)
    missing = [text for text in texts if text not in _fixture]
    if missing:
        if not recording_embeddings():
            raise KeyError(f"embedding fixture missing texts: {missing[:5]!r}")
        computed = await asyncio.to_thread(_model_embed, missing, model_name)
        for text, vector in zip(missing, computed, strict=True):
            _fixture[text] = vector
        _dirty = True
    vectors = [_fixture[text] for text in texts]
    _check_dim(vectors)
    return vectors


async def embed_texts(
    texts: list[str], model_name: str | None = None
) -> list[list[float]]:
    if not texts:
        return []
    return await _lookup_or_embed(texts, model_name)


async def embed_query(text: str, model_name: str | None = None) -> list[float]:
    return (await _lookup_or_embed([text], model_name))[0]
