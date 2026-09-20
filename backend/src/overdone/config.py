from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _discover_data_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data"
        if (candidate / "enrichment_rules.json").exists() or (
            candidate / "exercises.json"
        ).exists():
            return candidate
    return Path.cwd() / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Overdone"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    database_url: str = "postgresql+asyncpg://overdone:overdone@127.0.0.1:5432/overdone"
    ollama_base_url: str | None = None
    ollama_model: str = "llama3.2"
    data_dir: str | None = None
    enrichment_rules_path: str | None = None
    catalog_path: str | None = None
    bootstrap: bool = False

    @field_validator("ollama_base_url", mode="before")
    @classmethod
    def empty_url_is_unset(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    def resolved_data_dir(self) -> Path:
        if self.data_dir:
            return Path(self.data_dir)
        return _discover_data_dir()

    def resolved_enrichment_rules_path(self) -> Path:
        if self.enrichment_rules_path:
            return Path(self.enrichment_rules_path)
        return self.resolved_data_dir() / "enrichment_rules.json"

    def resolved_catalog_path(self) -> Path:
        if self.catalog_path:
            return Path(self.catalog_path)
        data = self.resolved_data_dir()
        for candidate in (
            data / "exercises.json",
            data / "free-exercise-db" / "exercises.json",
        ):
            if candidate.exists():
                return candidate
        return data / "exercises.json"

    def resolved_alembic_ini(self) -> Path:
        return Path(__file__).resolve().parents[2] / "alembic.ini"


settings = Settings()
