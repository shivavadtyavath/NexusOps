"""NexusOps Configuration."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_name: str = "NexusOps"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    # Groq (free)
    groq_api_key: str = ""
    groq_code_model: str = "llama-3.3-70b-versatile"
    groq_fast_model: str = "llama3-8b-8192"

    # GitHub
    github_token: str = ""
    github_webhook_secret: str = "nexusops-webhook-secret"

    # Database
    database_url: str = "sqlite+aiosqlite:///./nexusops.db"

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"

    # Analysis
    max_file_size_kb: int = 500
    max_files_per_pr: int = 50
    supported_languages: str = "python,javascript,typescript,go,java,rust,cpp"

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"

    # Auto-fix
    auto_create_pr: bool = False
    auto_fix_threshold: float = 0.80


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
