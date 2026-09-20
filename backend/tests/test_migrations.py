import asyncio

from sqlalchemy import text

from overdone.db import create_engine


def test_embedding_indexes_and_unit_checks(postgres_url: str) -> None:
    async def run() -> tuple[list[str], list[str]]:
        engine = create_engine(postgres_url)
        async with engine.connect() as connection:
            indexes = list(
                (
                    await connection.scalars(
                        text(
                            "SELECT indexname FROM pg_indexes "
                            "WHERE tablename = 'data_embeddings'"
                        )
                    )
                ).all()
            )
            checks = list(
                (
                    await connection.scalars(
                        text("SELECT conname FROM pg_constraint WHERE contype = 'c'")
                    )
                ).all()
            )
        await engine.dispose()
        return indexes, checks

    indexes, checks = asyncio.run(run())
    assert "ix_data_embeddings_embedding_hnsw" in indexes
    assert "ix_data_embeddings_metadata_gin" in indexes
    assert "ck_user_sets_unit" in checks
    assert "ck_user_benchmarks_unit" in checks
    assert "ck_user_settings_preferred_unit" in checks
