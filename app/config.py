"""Application settings (Pydantic). Reads from environment / .env.

See .env.example for all keys. Maps to ADR-0003 (hybrid LLM), ADR-0009 (model stack).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "local"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://bravo:bravo@localhost:5432/bravo"

    # Auth / security (SECURITY-RLS.md)
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720
    mcp_token_pepper: str = "change-me"

    # LLM Router — local default (ADR-0003 / ADR-0009)
    llm_local_base_url: str = "http://localhost:8001/v1"
    llm_local_model: str = "Qwen2.5-32B-Instruct-AWQ"
    llm_local_api_key: str = "dummy"

    # Cloud opt-in (default OFF; sensitive data never egresses — SECURITY-RLS.md §9)
    cloud_enabled: bool = False
    cloud_base_url: str = ""
    cloud_model: str = ""
    cloud_api_key: str = ""

    # Embedding — provider switch for the DEMO (machine too weak for local models).
    #   "local"            -> bge-m3 (ADR-0009, production default)
    #   "openai_compatible"-> cloud embeddings API (demo; corpus is non-sensitive guides)
    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    # Cloud embedding (used when embedding_provider == openai_compatible)
    cloud_embedding_base_url: str = ""
    cloud_embedding_model: str = ""
    cloud_embedding_api_key: str = ""

    # Demo: allow non-sensitive tasks (KB user-guide Q&A) to use the cloud LLM.
    demo_allow_cloud_answers: bool = False
    # Cross-encoder rerank (ViRanker) — local model; OFF for the cloud demo.
    rerank_enabled: bool = False

    # Worker
    redis_url: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
