"""Configuração centralizada via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação, carregadas do ambiente/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Postgres
    database_url: str = "postgresql+asyncpg://workshop:workshop@localhost:5432/workshop"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    minio_bucket_relatorios: str = "relatorios"

    # OpenAI (embeddings)
    openai_api_key: str = ""
    embed_model: str = "text-embedding-3-large"
    embed_dim: int = 3072

    # LLM
    llm_model_forte: str = "claude-sonnet-4-20250514"
    llm_model_rapido: str = "claude-haiku-4-20250514"

    # Agente RO
    agente_ro_password: str = "agente-ro"


@lru_cache
def get_settings() -> Settings:
    """Retorna settings cacheadas (singleton)."""
    return Settings()


settings = get_settings()
