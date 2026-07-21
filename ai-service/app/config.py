from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Service identity
    APP_NAME: str = 'nexus-ai-service'
    DEBUG: bool = False

    # Internal auth — must match backend INTERNAL_SERVICE_SECRET
    INTERNAL_SERVICE_SECRET: str = 'change-me-in-prod'

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = 'gpt-4o-mini'
    OPENAI_TEMPERATURE: float = 0.2

    # Optional GitHub App/user token. Read-only tools are disabled without it.
    GITHUB_TOKEN: str | None = None

    # PostgreSQL (pgvector)
    DATABASE_URL: str = 'postgresql+asyncpg://nexus:nexus@localhost:5432/nexus_dev'

    # Backend base URL (for internal callbacks)
    BACKEND_URL: str = 'http://localhost:8000'

    # Redis (for LangGraph checkpointer)
    REDIS_URL: str = 'redis://localhost:6379/1'

    # Embedding model
    EMBEDDING_MODEL: str = 'all-MiniLM-L6-v2'
    EMBEDDING_DIMENSION: int = 384

    MAX_DOCUMENT_SIZE_BYTES: int = 10 * 1024 * 1024
    DOCUMENT_CHUNK_SIZE: int = 1000
    DOCUMENT_CHUNK_OVERLAP: int = 150


@lru_cache
def get_settings() -> Settings:
    return Settings()
