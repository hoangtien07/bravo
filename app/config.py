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
    # RC-BE1: does each slot's model accept image (multimodal) input? A chat turn carrying an
    # image is routed to a vision-capable slot; if none, it FAILS LOUD instead of answering blind.
    # Default: local Qwen text-only (False), cloud gpt-4o vision (True). On a cloud-only gpt-4o
    # deployment both effectively resolve to the vision cloud slot.
    llm_local_vision: bool = False

    # Cloud opt-in (default OFF; sensitive data never egresses — SECURITY-RLS.md §9)
    cloud_enabled: bool = False
    cloud_base_url: str = ""
    cloud_model: str = ""
    cloud_api_key: str = ""
    cloud_vision: bool = True

    # Egress policy (ADR-0019/0022, v2 cloud-only). Governs router local-vs-cloud AND the
    # embedding/pipeline egress guards. Retires invariant #4 by CONFIG, not by deletion:
    #   "hybrid"     -> ADR-0003 behavior: fail-closed to local; sensitive pinned local (default).
    #   "cloud_only" -> no local backend exists; every call routes cloud; the sensitive-raise in
    #                   embed() is downgraded to an audit log (still recorded, never blocked).
    # The egress AUDIT trail (_audit_egress / bravo.egress log) is kept under BOTH policies — it
    # is the PDPL/91-2025 compliance artifact, not a sovereignty block.
    egress_policy: str = "hybrid"

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

    # Consultant Intelligence Layer. External-expert egress remains separately disabled.
    consultant_enabled: bool = False
    consultant_external_expert_enabled: bool = False
    consultant_rollout_percent: int = 100
    consultant_config_version: str = "consultant/v1"
    # Gap curation is the only scheduled Consultant job. It creates review-required internal
    # briefs; it never calls an external provider or activates knowledge.
    consultant_curation_enabled: bool = False
    consultant_curation_max_gaps: int = 100
    # Task-state expiry is separate from generic chat history/archival retention. It is disabled
    # until a data owner approves a duration and erasure/backup semantics.
    consultant_state_retention_enabled: bool = False
    consultant_state_retention_days: int = 0

    # Q9 vision OCR for scanned PDFs (ADR-0019 lifts the ADR-0009 OCR descope under cloud-only).
    # Needs pypdfium2 (optional dep) + a vision-capable cloud model. Numbers transcribed from a
    # scan stay quote-level (evidence_level=derived_summary) — never fed to the number verify-gate.
    vision_ocr_enabled: bool = False
    vision_model: str = ""                 # falls back to cloud_model when empty
    vision_max_pages: int = 20             # cap pages sent to the vision model per document
    # Rerank — biggest retrieval-quality lever (findings/J).
    #   provider "viranker" -> local cross-encoder (production)
    #   provider "llm"      -> listwise rerank via the cloud chat model (demo)
    rerank_enabled: bool = False
    rerank_provider: str = "viranker"
    # Structured output cho bước decide của agent (W1.3): json_object (cloud) / guided_json
    # (vLLM). Tắt -> chỉ dựa prompt + parser fallback. Bật mặc định (giảm output hỏng).
    structured_output: bool = True
    # Định dạng structured-output cho backend LOCAL (cloud luôn json_object):
    #   "guided_json"  -> vLLM/outlines ép schema (mạnh nhất; MẶC ĐỊNH production).
    #   "json_object"  -> endpoint OpenAI-compatible dùng làm "local" (vd demo trỏ OpenAI) —
    #                     guided_json KHÔNG được OpenAI chấp nhận (lỗi 400) nên phải json_object.
    #   "off"          -> không ép (chỉ dựa prompt).
    local_structured_mode: str = Field("guided_json", validation_alias="LOCAL_STRUCTURED_MODE")
    # W1.4: lượt tri thức -> COMPOSE câu trả lời bằng chat_stream (token THẬT chảy ra SSE).
    # Đây là LỜI GỌI LLM THỨ HAI (tái sinh câu trả lời) nên OFF mặc định (không double-cost,
    # test/eval ổn định); demo bật STREAM_COMPOSE_ANSWER=true để có streaming token thật. Khi
    # OFF: phát answer đã quyết ở bước decide dưới dạng một delta (đúng, không cắt giả).
    stream_compose_answer: bool = False
    # P0b: single-generation streaming. Khi ON (mặc định), lượt tri thức STREAM thẳng field
    # `answer` của bước DECIDE token-by-token (KHÔNG sinh lần 2 như compose — triệt tiêu C1 +
    # giảm ~½ chi phí + không re-gửi ảnh). Hold-back khối kiến-thức-chung/abstain để guard chạy
    # TRƯỚC khi phát (F3). Lượt tài chính LUÔN buffered (verify-gate, invariant #3) bất kể cờ này.
    stream_decide_answer: bool = True
    # M3: hard timeout (s) for a single retrieval call so a hung pgvector query can't stall a turn.
    retrieval_timeout_s: float = 20.0
    # P1: multi-turn image handling. Re-send recent conversation images to the vision model so the
    # assistant "remembers" them across turns — but each re-send is a fresh cloud egress of the same
    # (often PII) image, so cap it hard (F-2 data-minimization). attach_image_turns documents intent;
    # attach_image_max is the operative per-prompt cap on total images.
    attach_image_turns: int = 3
    attach_image_max: int = 4
    # M4: text attachments — inject FULL text for the N most-recent, a bounded DIGEST for older
    # ones (deterministic-by-recency, so a long conversation doesn't silently drop context or blow
    # the context window based on unrelated history length).
    attach_text_full: int = 3
    attach_text_digest_chars: int = 1200
    # ADR-0024: the per-conversation lock is in-process (đủ cho single-worker). BẬT cờ này khi chạy
    # NHIỀU worker/tiến trình để thêm khoá Postgres advisory (pg_try_advisory_lock trên hashtext của
    # session_id) — chống hai worker cùng chạy một hội thoại. Default off (chưa deploy multi-worker).
    use_pg_advisory_lock: bool = False
    # Ngưỡng tương đồng cosine tối thiểu cho truy hồi dense (0..1). Chunk dưới ngưỡng bị loại
    # để tránh "nhiễu" (vd câu hỏi 'mua' kéo về chunk 'bán' điểm thấp). 0 = tắt. Lexical (mã/số)
    # không bị ngưỡng này. Rỗng sau lọc -> agent trả "không tìm thấy" (zero-hallucination).
    retrieval_min_score: float = 0.12
    # Q6: after rerank, expand each finalist chunk with its sibling chunks from the same
    # (source, heading section) so long procedures cut at ~900 tokens are answered whole.
    retrieval_expand_sections: bool = True
    retrieval_section_token_cap: int = 2000     # per expanded section
    retrieval_expand_top: int = 6               # expand only the top-N finalists

    def resolved_min_score(self) -> float:
        """Cosine floor calibrated PER embedding model (Q11) — different models have different
        score distributions, so a single hard-coded 0.12 is wrong when the model changes. Falls
        back to `retrieval_min_score` for unknown models (no behavior change until calibrated)."""
        by_model = {
            "BAAI/bge-m3": 0.12,
            "text-embedding-3-small": 0.12,
            "text-embedding-3-large": 0.12,
            "gemini-embedding-001": 0.12,
        }
        return by_model.get(self.embedding_model, self.retrieval_min_score)

    # Worker
    redis_url: str = "redis://localhost:6379/0"
    # Ingest inline (no arq/Redis). Test/dev fallback so the suite runs without a worker.
    # Prod runs the arq worker and enqueues -> keep False.
    ingest_sync: bool = False

    # Agent turn token budget (circuit breaker, loop.Budget). v2 cloud-only raises this from the
    # on-prem 8k floor because a single chat attachment inject (≤50k tokens) must fit within one
    # turn; gpt-4o-class context is 128k. max_steps/deadline stay tight as the real cost guard.
    agent_max_tokens: int = 120_000

    # Frontier runtime migration. "legacy" keeps the current constrained ReAct loop; "openai"
    # selects the OpenAI Agents SDK adapter once its canary is enabled.  The switch is explicit so
    # a provider/runtime regression never silently changes the deployed chatbot behavior.
    agent_runtime: str = "legacy"              # legacy | openai | canary
    agent_runtime_canary_percent: int = 0       # 0..100; evaluated per user in the API layer
    openai_agents_fast_model: str = "gpt-5.4-mini"
    openai_agents_reasoning_model: str = "gpt-5.6-sol"
    openai_agents_max_turns: int = 8
    openai_agents_trace_sensitive_data: bool = False

    # Frontier optional surfaces remain opt-in. Realtime is not exposed until a deployment has
    # an authenticated transport; computer-use is proposal-only and blocked by policy first.
    realtime_enabled: bool = False
    realtime_model: str = "gpt-realtime"
    computer_use_enabled: bool = False
    computer_use_allowed_domains: str = ""
    computer_use_max_steps: int = 8

    # Chat attachments (Track 3). Text at/under the cap is injected full-text into the prompt;
    # oversized text falls back to RAG-ingest into the user's personal workspace. 50k leaves
    # headroom for retrieval context + history + output inside a 128k window (LibreChat uses 100k
    # for the file alone; we stack retrieval on top, so pick lower).
    attachment_inject_token_cap: int = 50_000
    attachment_max_bytes: int = 30 * 1024 * 1024        # 30 MB doc / image ceiling

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
        if self.agent_runtime not in {"legacy", "openai", "canary"}:
            raise RuntimeError("[boot-guard] agent_runtime must be legacy, openai, or canary.")
        if not 0 <= self.agent_runtime_canary_percent <= 100:
            raise RuntimeError("[boot-guard] agent_runtime_canary_percent must be 0..100.")
        if not 0 <= self.consultant_rollout_percent <= 100:
            raise RuntimeError("[boot-guard] consultant_rollout_percent must be 0..100.")
        if not 1 <= self.consultant_curation_max_gaps <= 1000:
            raise RuntimeError("[boot-guard] consultant_curation_max_gaps must be 1..1000.")
        if self.consultant_state_retention_enabled and not 1 <= self.consultant_state_retention_days <= 3650:
            raise RuntimeError(
                "[boot-guard] consultant_state_retention_days must be 1..3650 when retention is enabled."
            )
        if self.computer_use_max_steps < 1 or self.computer_use_max_steps > 50:
            raise RuntimeError("[boot-guard] computer_use_max_steps must be 1..50.")
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
        # Cloud-only (ADR-0019): there is NO local backend to fall back to, so the cloud path
        # must be fully configured or the app cannot answer at all -> fail-closed at boot.
        if self.egress_policy == "cloud_only" and not (
            self.cloud_enabled and self.cloud_api_key and self.cloud_base_url and self.cloud_model
        ):
            raise RuntimeError(
                "[boot-guard] egress_policy=cloud_only yêu cầu cloud_enabled + "
                "cloud_api_key + cloud_base_url + cloud_model (không còn backend local)."
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
