"""Application settings loaded from environment variables."""
import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Configuration
    google_api_key: str = Field(..., description="Google AI Studio API key")
    google_model: str = Field(
        default="gemini-1.5-flash",
        description="Gemini model name"
    )
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=700, ge=100, le=4000)
    llm_timeout: int = Field(default=20, description="LLM request timeout in seconds")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://grounded:grounded@localhost:5432/grounded"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Embeddings
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dim: int = Field(default=384)

    # Application
    workspaces_dir: Path = Field(default=Path("./workspaces"))
    log_level: str = Field(default="INFO")

    # Security
    admin_password: Optional[str] = Field(default=None, description="Optional admin password")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=30)
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL (1 hour)")

    # Retrieval
    default_top_k: int = Field(default=5)
    default_min_score: float = Field(default=0.35)

    @property
    def workspaces_path(self) -> Path:
        """Get absolute path to workspaces directory."""
        if self.workspaces_dir.is_absolute():
            return self.workspaces_dir
        return Path.cwd() / self.workspaces_dir


# Global settings instance
settings = Settings()
