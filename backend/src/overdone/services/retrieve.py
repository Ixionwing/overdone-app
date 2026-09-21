from __future__ import annotations

import re
from datetime import date

from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from overdone.ingest.embed import embed_texts
from overdone.ingest.vectorstore import OverdoneVectorStore, note_node
from overdone.models.embeddings import DataEmbedding
from overdone.models.exercise import Exercise, ExerciseEnrichment
from overdone.models.user_log import UserSession
from overdone.services.vectors import search_embeddings

_QUALITATIVE = re.compile(r"\b(tight|pain|sore|ache|hurt|tweak)\b", re.I)


class RetrievedChunk(BaseModel):
    kind: str
    text: str
    source_id: str | None = None
    exercise_id: str | None = None
    session_id: str | None = None
    logged_on: date | None = None
    score: float = 0.0


class RetrieveResult(BaseModel):
    exercises: list[RetrievedChunk] = Field(default_factory=list)
    notes: list[RetrievedChunk] = Field(default_factory=list)


def relative_day(logged_on: date, today: date | None = None) -> str:
    days = ((today or date.today()) - logged_on).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    return f"{days} days ago"


def is_qualitative_note(text: str) -> bool:
    return bool(_QUALITATIVE.search(text))


def note_banner(logged_on: date, quote: str, today: date | None = None) -> str:
    return f"Note from {relative_day(logged_on, today)}: '{quote}'"


async def rebuild_session_notes(session: AsyncSession) -> None:
    store = OverdoneVectorStore(session=session)
    await session.execute(
        delete(DataEmbedding).where(
            DataEmbedding.metadata_["kind"].astext == "session_note"
        )
    )
    logged = list(
        (
            await session.scalars(
                select(UserSession)
                .options(selectinload(UserSession.sets))
                .order_by(UserSession.logged_on)
            )
        ).all()
    )
    notes = [
        (row, row.notes.strip()) for row in logged if row.notes and row.notes.strip()
    ]
    if not notes:
        return
    embeddings = await embed_texts([text for _row, text in notes])
    nodes = [
        note_node(
            session_id=str(row.id),
            logged_on=row.logged_on.isoformat(),
            text=text,
            embedding=embedding,
        )
        for (row, text), embedding in zip(notes, embeddings, strict=True)
    ]
    await store.async_add(nodes)


def _chunk_from_row(row: DataEmbedding, score: float) -> RetrievedChunk:
    meta = row.metadata_ or {}
    logged_raw = meta.get("logged_on")
    logged_on = date.fromisoformat(logged_raw) if logged_raw else None
    return RetrievedChunk(
        kind=str(meta.get("kind") or ""),
        text=row.text,
        source_id=meta.get("source_id") or meta.get("ref_doc_id"),
        exercise_id=meta.get("exercise_id"),
        session_id=meta.get("session_id"),
        logged_on=logged_on,
        score=score,
    )


async def _search(
    session: AsyncSession,
    *,
    query: str,
    kind: str,
    limit: int,
    source_ids: list[str] | None = None,
    exercise_ids: list[str] | None = None,
) -> list[RetrievedChunk]:
    rows = await search_embeddings(
        session,
        query=query,
        kinds=(kind,),
        limit=limit,
        source_ids=source_ids,
        exercise_ids=exercise_ids,
    )
    return [_chunk_from_row(chunk, score) for chunk, score in rows]


async def _terms_for(session: AsyncSession, exercise_ids: list[str]) -> set[str]:
    terms: set[str] = set()
    for raw in exercise_ids:
        if not raw.isdigit():
            continue
        exercise = await session.get(Exercise, int(raw))
        enrich = await session.get(ExerciseEnrichment, int(raw))
        if exercise is not None:
            for muscle in [*exercise.primary_muscles, *exercise.secondary_muscles]:
                terms.add(muscle.casefold())
        if enrich is not None:
            for joint, value in (enrich.joints or {}).items():
                if value and float(value) > 0:
                    terms.add(str(joint).casefold())
    return terms


async def _keyword_notes(
    session: AsyncSession, terms: set[str]
) -> list[RetrievedChunk]:
    if not terms:
        return []
    rows = list(
        (
            await session.scalars(
                select(DataEmbedding).where(
                    DataEmbedding.metadata_["kind"].astext == "session_note"
                )
            )
        ).all()
    )
    hits: list[RetrievedChunk] = []
    for row in rows:
        haystack = row.text.casefold()
        if any(term in haystack for term in terms):
            hits.append(_chunk_from_row(row, 1.0))
    return hits


async def retrieve_context(
    session: AsyncSession,
    *,
    exercise_ids: list[str],
    prompt: str,
) -> RetrieveResult:
    bound = [item for item in exercise_ids if item]
    exercises = (
        await _search(
            session,
            query=prompt,
            kind="exercise",
            limit=4,
            exercise_ids=bound or None,
        )
        if bound
        else []
    )
    semantic_notes = [
        note
        for note in await _search(session, query=prompt, kind="session_note", limit=4)
        if note.text.strip() and note.score >= 0.35
    ]
    keyword_notes = await _keyword_notes(session, await _terms_for(session, bound))
    notes: list[RetrievedChunk] = []
    seen: set[str] = set()
    for note in [*keyword_notes, *semantic_notes]:
        if not note.text.strip() or not is_qualitative_note(note.text):
            continue
        key = note.source_id or note.text
        if key in seen:
            continue
        seen.add(key)
        notes.append(note)
    return RetrieveResult(exercises=exercises, notes=notes)
