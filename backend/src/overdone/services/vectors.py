from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from overdone.ingest.embed import embed_query
from overdone.models.embeddings import DataEmbedding


async def search_embeddings(
    session: AsyncSession,
    *,
    query: str,
    kinds: Sequence[str],
    limit: int | None = None,
    source_ids: Sequence[str] | None = None,
    exercise_ids: Sequence[str] | None = None,
    distinct_on_kind: bool = False,
) -> list[tuple[DataEmbedding, float]]:
    vector = await embed_query(query)
    similarity = (1 - DataEmbedding.embedding.cosine_distance(vector)).label("sim")
    kind_col = DataEmbedding.metadata_["kind"].astext
    stmt = select(DataEmbedding, similarity).where(kind_col.in_(list(kinds)))
    if source_ids:
        stmt = stmt.where(
            DataEmbedding.metadata_["source_id"].astext.in_(list(source_ids))
        )
    if exercise_ids:
        stmt = stmt.where(
            DataEmbedding.metadata_["exercise_id"].astext.in_(list(exercise_ids))
        )
    if distinct_on_kind:
        stmt = stmt.distinct(kind_col).order_by(
            kind_col, DataEmbedding.embedding.cosine_distance(vector)
        )
    else:
        stmt = stmt.order_by(DataEmbedding.embedding.cosine_distance(vector))
        if limit is not None:
            stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).all()
    return [(chunk, float(score)) for chunk, score in rows]
