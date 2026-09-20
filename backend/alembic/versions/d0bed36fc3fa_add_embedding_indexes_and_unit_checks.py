"""add embedding indexes and unit checks

Revision ID: d0bed36fc3fa
Revises: 132f6d84a052
Create Date: 2026-09-20 13:55:06.589512

"""

from collections.abc import Sequence

from alembic import op

revision: str = "d0bed36fc3fa"
down_revision: str | Sequence[str] | None = "132f6d84a052"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_data_embeddings_embedding_hnsw "
        "ON data_embeddings USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_data_embeddings_metadata_gin "
        "ON data_embeddings USING gin (metadata_)"
    )
    op.create_check_constraint(
        "unit",
        "user_sets",
        "unit IN ('lb', 'kg')",
    )
    op.create_check_constraint(
        "unit",
        "user_benchmarks",
        "unit IN ('lb', 'kg')",
    )
    op.create_check_constraint(
        "preferred_unit",
        "user_settings",
        "preferred_unit IN ('lb', 'kg')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_settings_preferred_unit", "user_settings")
    op.drop_constraint("ck_user_benchmarks_unit", "user_benchmarks")
    op.drop_constraint("ck_user_sets_unit", "user_sets")
    op.execute("DROP INDEX IF EXISTS ix_data_embeddings_metadata_gin")
    op.execute("DROP INDEX IF EXISTS ix_data_embeddings_embedding_hnsw")
