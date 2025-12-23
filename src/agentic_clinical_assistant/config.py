"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "agentic-clinical-assistant"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/clinical_assistant"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # FAISS
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    FAISS_DIMENSION: int = 384

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-west1-gcp"
    PINECONE_INDEX_NAME: str = "clinical-assistant"

    # Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: str = ""
    WEAVIATE_CLASS_NAME: str = "ClinicalDocument"

    # LLM (OpenAI)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # Agent
    DEFAULT_VECTOR_BACKEND: str = "faiss"
    MAX_RETRIEVAL_RESULTS: int = 10
    ENABLE_MULTI_BACKEND_RETRIEVAL: bool = False

    # Safety & Compliance
    ENABLE_PHI_REDACTION: bool = True
    ENABLE_GROUNDING_VERIFICATION: bool = True
    ENABLE_PROMPT_INJECTION_DETECTION: bool = True

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    ENABLE_METRICS: bool = True

    # Session & Memory
    SESSION_EXPIRY_HOURS: int = 24
    ENABLE_SESSION_MEMORY: bool = True
    ENABLE_POLICY_MEMORY: bool = True

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS_STR: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        alias="ALLOWED_ORIGINS",
        description="Comma-separated list of allowed CORS origins",
    )

    # Evaluation
    EVAL_DATASET_PATH: str = "./data/eval_dataset.json"
    ENABLE_NIGHTLY_EVAL: bool = True

    @computed_field
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_STR.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

