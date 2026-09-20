from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from overdone.models.base import Base


class DataEmbedding(Base):
    __tablename__ = "data_embeddings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata_", JSONB, nullable=True)
    node_id: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))


Index(
    "ix_data_embeddings_ref_doc_id",
    DataEmbedding.metadata_["ref_doc_id"].astext,
    postgresql_using="btree",
)
