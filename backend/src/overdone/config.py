from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Overdone"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    database_url: str = "postgresql+asyncpg://overdone:overdone@127.0.0.1:5432/overdone"
    ollama_base_url: str | None = None
    ollama_model: str = "llama3.2"

    @field_validator("ollama_base_url", mode="before")
    @classmethod
    def empty_url_is_unset(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


settings = Settings()
