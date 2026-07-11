"""Application settings (Pydantic). Reads from environment / .env.

See .env.example for all keys. Maps to ADR-0003 (hybrid LLM), ADR-0009 (model stack).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    env: str = "local"
    log_level: str = "INFO"

    # Config-as-data (ADR-0018 packaging): thư mục OVERLAY chứa knowledge/rule runtime (COA, mapping,
    # statutory...). Bind-mount read-only để cập nhật rule KHÔNG rebuild image; file thiếu -> fallback
    # bản in-package (bravo ship CHẠY ĐƯỢC, khác agent-ai ship rỗng). Đọc lúc BOOT, single-tenant.
    knowledge_dir: str = Field("", validation_alias="BRAVO_KNOWLEDGE_DIR")
    # Manifest per-deploy (deploy/site.yaml): enabled_verticals + phòng ban + flags. Đọc 1 lần lúc
    # boot trong validate_boot() (fail-closed). Rỗng = bỏ qua (dev/demo không bắt buộc).
    site_config: str = Field("", validation_alias="SITE_CONFIG")
    app_root: str = Field("", validation_alias="APP_ROOT")
    data_root: str = Field("", validation_alias="DATA_ROOT")
    corpus_root: str = Field("", validation_alias="CORPUS_ROOT")
    upload_root: str = Field("", validation_alias="UPLOAD_ROOT")
    private_data_root: str = Field("", validation_alias="PRIVATE_DATA_ROOT")
    data_runtime_policy: str = Field(
        "file_system/bravo_data_runtime_policy.yaml",
        validation_alias="DATA_RUNTIME_POLICY",
    )

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
    # Structured output cho bước decide của agent (W1.3): json_object (cloud) / guided_json
    # (vLLM). Tắt -> chỉ dựa prompt + parser fallback. Bật mặc định (giảm output hỏng).
    structured_output: bool = True
    # W1.4: lượt tri thức -> COMPOSE câu trả lời bằng chat_stream (token THẬT chảy ra SSE).
    # Đây là LỜI GỌI LLM THỨ HAI (tái sinh câu trả lời) nên OFF mặc định (không double-cost,
    # test/eval ổn định); demo bật STREAM_COMPOSE_ANSWER=true để có streaming token thật. Khi
    # OFF: phát answer đã quyết ở bước decide dưới dạng một delta (đúng, không cắt giả).
    stream_compose_answer: bool = False
    # Ngưỡng tương đồng cosine tối thiểu cho truy hồi dense (0..1). Chunk dưới ngưỡng bị loại
    # để tránh "nhiễu" (vd câu hỏi 'mua' kéo về chunk 'bán' điểm thấp). 0 = tắt. Lexical (mã/số)
    # không bị ngưỡng này. Rỗng sau lọc -> agent trả "không tìm thấy" (zero-hallucination).
    retrieval_min_score: float = 0.12

    # Worker
    redis_url: str = "redis://localhost:6379/0"

    # MCP server scoped-by-token tại /mcp (W1.5). Tắt nếu không muốn expose.
    mcp_enabled: bool = True

    # --- Observability (W2.2) — self-host, air-gap ---
    metrics_enabled: bool = True                 # phơi /metrics (Prometheus scrape)
    otel_exporter_endpoint: str = ""             # OTLP/HTTP collector; rỗng = tắt tracing

    # --- Rate-limit + GPU concurrency (W2.3) ---
    rate_limit_per_minute: int = 30              # req/phút/người cho endpoint chat; 0 = tắt
    llm_max_concurrency: int = 2                 # số lời gọi LLM đồng thời (GPU on-prem ~1-2)

    # --- Cost tracking (W2.4) — ước phí từ token usage thật (đơn vị tuỳ chọn: USD/1M token) ---
    cost_per_1m_prompt_tokens: float = 0.0
    cost_per_1m_completion_tokens: float = 0.0

    # --- OIDC SSO (W2.1) — bật khi có IdP (Keycloak self-host federate LDAP/AD) ---
    oidc_enabled: bool = False
    oidc_issuer: str = ""                        # vd http://keycloak:8080/realms/bravo
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = ""                  # vd https://app/api/auth/oidc/callback
    session_secret: str = "change-me-session"    # SessionMiddleware (OIDC state/nonce)

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
        # Manifest deploy (nếu cấu hình): validate ở MỌI env — fail-closed khi sai (config-as-data).
        if self.site_config:
            from app.site_config import load_site_config
            load_site_config(self.site_config)
        self.validate_data_runtime_policy()
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

    def data_policy_variables(self) -> dict[str, str]:
        from pathlib import Path

        app_root = Path(self.app_root or Path.cwd()).resolve()
        data_root = Path(self.data_root or app_root / "data").resolve()
        corpus_root = Path(self.corpus_root or app_root / "file_system").resolve()
        return {
            "APP_ROOT": str(app_root),
            "DATA_ROOT": str(data_root),
            "CORPUS_ROOT": str(corpus_root),
            "UPLOAD_ROOT": str(Path(self.upload_root or data_root / "uploads").resolve()),
            "PRIVATE_DATA_ROOT": str(
                Path(self.private_data_root or data_root / "private").resolve()
            ),
        }

    def validate_data_runtime_policy(self) -> None:
        from pathlib import Path

        from app.eval.bravo_data_audit import audit_data_layout
        from app.eval.bravo_data_policy import (
            ensure_runtime_policy_paths,
            load_data_runtime_policy,
        )

        policy_path = Path(self.data_runtime_policy)
        if not policy_path.is_absolute():
            policy_path = Path(self.data_policy_variables()["APP_ROOT"]) / policy_path
        policy = load_data_runtime_policy(policy_path, variables=self.data_policy_variables())
        ensure_runtime_policy_paths(policy)
        audit = audit_data_layout(policy_path=policy_path, policy=policy)
        errors: list[str] = []
        errors.extend(f"policy: {issue}" for issue in audit.policy_errors)
        errors.extend(f"required path missing: {path}" for path in audit.required_path_missing)
        errors.extend(f"manifest missing file: {path}" for path in audit.missing_manifest_files)
        errors.extend(
            f"active duplicate sha256 {group.hash}: {', '.join(group.paths)}"
            for group in audit.active_duplicate_hash_groups
        )
        errors.extend(
            f"unmanifested ingestible violates policy: {path}"
            for path in audit.unmanifested_ingestible_errors
        )
        if errors:
            raise RuntimeError("[boot-guard] data runtime policy invalid: " + "; ".join(errors[:10]))
        if self.cloud_enabled and not (self.cloud_api_key and self.cloud_base_url):
            raise RuntimeError(
                "[boot-guard] cloud_enabled=true nhưng thiếu cloud_api_key/cloud_base_url."
            )
        # W2.6: tự-duyệt là lỗ hổng maker-checker ở prod -> cấm.
        if self.allow_self_approval:
            raise RuntimeError(
                "[boot-guard] allow_self_approval=true KHÔNG được phép ở prod (maker-checker)."
            )
        # OIDC bật -> phải đủ cấu hình + session_secret mạnh (không mặc định).
        if self.oidc_enabled:
            if self.session_secret in weak or self.session_secret == "change-me-session" \
                    or len(self.session_secret) < 16:
                raise RuntimeError(
                    "[boot-guard] oidc_enabled=true nhưng session_secret còn mặc định/quá ngắn."
                )
            if not (self.oidc_issuer and self.oidc_client_id and self.oidc_client_secret
                    and self.oidc_redirect_uri):
                raise RuntimeError(
                    "[boot-guard] oidc_enabled=true nhưng thiếu oidc_issuer/client_id/"
                    "client_secret/redirect_uri."
                )


@lru_cache
def get_settings() -> Settings:
    return Settings()
