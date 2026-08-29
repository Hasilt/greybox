"""Application configuration.

All settings are read from environment variables prefixed with ``GREYBOX_``
(e.g. ``GREYBOX_QDRANT_URL``). Defaults target the docker-compose network.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GREYBOX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Infrastructure endpoints ---
    qdrant_url: str = "http://qdrant:6333"
    redis_url: str = "redis://redis:6379"

    # --- Vector store ---
    qdrant_collection: str = "greybox_kb"

    # --- Embeddings ---
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # --- Caching ---
    cache_ttl_seconds: int = 3600

    # --- Drift detection ---
    drift_threshold: float = 0.15

    # --- LLM answer generation (optional) ---
    llm_provider: str = "ollama"  # "ollama" | "openai" | "none"
    ollama_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.2"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30.0

    # --- Ingestion / chunking ---
    chunk_size: int = 500  # words (~tokens); see README limitations
    chunk_overlap: int = 100
    data_dir: str = "/data"

    # --- Drift baseline artifact ---
    baseline_centroid_path: str = "/data/baseline_centroid.npy"

    # --- Metrics ---
    metrics_window: int = 500

    @property
    def documents_dir(self) -> str:
        return f"{self.data_dir.rstrip('/')}/documents"

    @property
    def evaluation_path(self) -> str:
        return f"{self.data_dir.rstrip('/')}/evaluation/questions.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
