from collections.abc import Sequence
from typing import Any

from llama_index.core.schema import BaseNode, MetadataMode, TextNode
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    VectorStoreQuery,
    VectorStoreQueryResult,
)
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from overdone.models.embeddings import DataEmbedding


class OverdoneVectorStore(BasePydanticVectorStore):
    """LlamaIndex writer over the Alembic `data_embeddings` table."""

    stores_text: bool = True
    is_embedding_query: bool = True
    session: Any = None

    @property
    def client(self) -> AsyncSession:
        return self.session

    def add(self, nodes: Sequence[BaseNode], **kwargs: Any) -> list[str]:
        raise RuntimeError("use async_add with an AsyncSession")

    async def async_add(self, nodes: Sequence[BaseNode], **kwargs: Any) -> list[str]:
        ids: list[str] = []
        for node in nodes:
            metadata = dict(node.metadata or {})
            ref = node.ref_doc_id or metadata.get("source_id") or node.node_id
            metadata["ref_doc_id"] = ref
            self.session.add(
                DataEmbedding(
                    text=node.get_content(metadata_mode=MetadataMode.NONE),
                    metadata_=metadata,
                    node_id=node.node_id,
                    embedding=list(node.get_embedding()),
                )
            )
            ids.append(node.node_id)
        await self.session.flush()
        return ids

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        raise RuntimeError("use adelete with an AsyncSession")

    async def adelete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        await self.session.execute(
            delete(DataEmbedding).where(
                DataEmbedding.metadata_["ref_doc_id"].astext == ref_doc_id
            )
        )

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        """Reads go through retrieve_context, not this LlamaIndex query()."""
        del query, kwargs
        return VectorStoreQueryResult(nodes=[], similarities=[], ids=[])


def exercise_node(
    *,
    source_id: str,
    exercise_id: str,
    text: str,
    embedding: list[float],
) -> TextNode:
    node = TextNode(
        text=text,
        id_=source_id,
        metadata={
            "kind": "exercise",
            "source_id": source_id,
            "exercise_id": exercise_id,
            "ref_doc_id": source_id,
        },
    )
    node.embedding = embedding
    return node


def name_node(
    *,
    source_id: str,
    exercise_id: str,
    text: str,
    embedding: list[float],
    label: str,
) -> TextNode:
    node_id = f"{source_id}::name::{label}"
    node = TextNode(
        text=text,
        id_=node_id,
        metadata={
            "kind": "exercise_name",
            "source_id": source_id,
            "exercise_id": exercise_id,
            "ref_doc_id": source_id,
        },
    )
    node.embedding = embedding
    return node


def note_node(
    *,
    session_id: str,
    logged_on: str,
    text: str,
    embedding: list[float],
) -> TextNode:
    node_id = f"session-note-{session_id}"
    node = TextNode(
        text=text,
        id_=node_id,
        metadata={
            "kind": "session_note",
            "source_id": node_id,
            "ref_doc_id": node_id,
            "session_id": session_id,
            "logged_on": logged_on,
        },
    )
    node.embedding = embedding
    return node
