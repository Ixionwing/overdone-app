"""create catalog and baseline tables

Revision ID: 132f6d84a052
Revises:
Create Date: 2026-09-20 06:36:58.835394

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "132f6d84a052"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.create_table(
        "data_embeddings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("metadata_", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("node_id", sa.String(), nullable=True),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_embeddings")),
    )
    op.create_index(
        "ix_data_embeddings_ref_doc_id",
        "data_embeddings",
        [sa.literal_column("(metadata_ ->> 'ref_doc_id')")],
        unique=False,
        postgresql_using="btree",
    )
    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("force", sa.String(length=64), nullable=True),
        sa.Column("level", sa.String(length=64), nullable=True),
        sa.Column("mechanic", sa.String(length=64), nullable=True),
        sa.Column("equipment", sa.String(length=64), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("primary_muscles", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("secondary_muscles", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("instructions", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exercises")),
        sa.UniqueConstraint("source_id", name=op.f("uq_exercises_source_id")),
    )
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("logged_on", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_sessions")),
    )
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("preferred_unit", sa.String(length=2), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_settings")),
    )
    op.create_table(
        "exercise_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name=op.f("fk_exercise_aliases_exercise_id_exercises"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exercise_aliases")),
        sa.UniqueConstraint("alias", name=op.f("uq_exercise_aliases_alias")),
    )
    op.create_table(
        "exercise_enrichment",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("axial_factor", sa.Float(), nullable=False),
        sa.Column("cns_factor", sa.Float(), nullable=False),
        sa.Column("joints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name=op.f("fk_exercise_enrichment_exercise_id_exercises"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("exercise_id", name=op.f("pk_exercise_enrichment")),
    )
    op.create_table(
        "user_benchmarks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=True),
        sa.Column("exercise_name", sa.String(length=255), nullable=False),
        sa.Column("one_rm_kg", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=2), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name=op.f("fk_user_benchmarks_exercise_id_exercises"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_benchmarks")),
    )
    op.create_table(
        "user_sets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=True),
        sa.Column("exercise_name", sa.String(length=255), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=2), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name=op.f("fk_user_sets_exercise_id_exercises"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["user_sessions.id"],
            name=op.f("fk_user_sets_session_id_user_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_sets")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_sets")
    op.drop_table("user_benchmarks")
    op.drop_table("exercise_enrichment")
    op.drop_table("exercise_aliases")
    op.drop_table("user_settings")
    op.drop_table("user_sessions")
    op.drop_table("exercises")
    op.drop_index(
        "ix_data_embeddings_ref_doc_id",
        table_name="data_embeddings",
        postgresql_using="btree",
    )
    op.drop_table("data_embeddings")
    op.execute(sa.text("DROP EXTENSION IF EXISTS vector"))
    # ### end Alembic commands ###
