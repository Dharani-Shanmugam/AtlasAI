from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "AtlasAI"
    app_env: str = "development"
    debug: bool = True

    # Persistence
    database_url: str = "sqlite+aiosqlite:///./data/atlas.db"
    data_dir: Path = Path("./data")

    # LLM provider (Groq is OpenAI-compatible)
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = Field(default=0.4, ge=0.0, le=2.0)

    # Embeddings (local — no key needed)
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Retrieval & chunking
    retrieval_top_k: int = Field(default=5, ge=1, le=50)
    chunk_size: int = Field(default=800, ge=100)
    chunk_overlap: int = Field(default=150, ge=0)

    # CORS
    cors_origins: Annotated[list[str] | str, NoDecode] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_list(cls, value: object) -> object:
        """Accept JSON (`["http://a"]`) or comma-separated strings."""
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def vector_store_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def is_llm_configured(self) -> bool:
        return bool(self.groq_api_key and self.groq_api_key != "your-groq-api-key")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
