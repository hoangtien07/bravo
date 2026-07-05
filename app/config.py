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
    # Maker-checker (WP-E): mặc định CẤM người tạo tự duyệt draft của mình (SOX/ISA).
    allow_self_approval: bool = False

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
    # Rerank — biggest retrieval-quality lever (findings/J).
    #   provider "viranker" -> local cross-encoder (production)
    #   provider "llm"      -> listwise rerank via the cloud chat model (demo)
    rerank_enabled: bool = False
    rerank_provider: str = "viranker"
    # Ngưỡng tương đồng cosine tối thiểu cho truy hồi dense (0..1). Chunk dưới ngưỡng bị loại
    # để tránh "nhiễu" (vd câu hỏi 'mua' kéo về chunk 'bán' điểm thấp). 0 = tắt. Lexical (mã/số)
    # không bị ngưỡng này. Rỗng sau lọc -> agent trả "không tìm thấy" (zero-hallucination).
    retrieval_min_score: float = 0.12

    # Worker
    redis_url: str = "redis://localhost:6379/0"

    # CORS: origin được phép gọi API từ trình duyệt khác origin. RỖNG ở prod (SPA serve
    # same-origin từ FastAPI -> không cần CORS). Dev Vite (:5173) proxy /api hoặc gọi thẳng
    # -> đặt "http://localhost:5173". Danh sách phân tách bằng dấu phẩy.
    cors_allow_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    def validate_boot(self) -> None:
        """Fail-closed boot guard (DEPLOY-DEMO.md hứa điều này). Ở staging/production:
        chặn khởi động nếu secret còn mặc định/quá ngắn, hoặc bật cloud mà thiếu key.
        Ở env=local (demo) là no-op để không cản trở phát triển."""
        if self.env not in {"staging", "production", "prod"}:
            return
        weak = {"change-me", "change-me-in-production", "change-me-256-bit-random"}
        for name in ("jwt_secret", "mcp_token_pepper"):
            val = getattr(self, name)
            if val in weak or len(val) < 16:
                raise RuntimeError(
                    f"[boot-guard] {name} còn giá trị mặc định/quá ngắn ở env={self.env}. "
                    "Đặt secret ngẫu nhiên ≥16 ký tự trước khi chạy production (fail-closed)."
                )
        if self.cloud_enabled and not (self.cloud_api_key and self.cloud_base_url):
            raise RuntimeError(
                "[boot-guard] cloud_enabled=true nhưng thiếu cloud_api_key/cloud_base_url."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
