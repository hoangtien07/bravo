"""Observability (W2.2) — metrics Prometheus + tracing OpenTelemetry, self-host/air-gap.

Bật/tắt qua settings:
  - metrics_enabled -> phơi /metrics (prometheus-fastapi-instrumentator) + counter riêng
    cho LLM (backend/tokens) và tool-call. KHÔNG gửi ra ngoài — Prometheus tự scrape.
  - otel_exporter_endpoint (rỗng = tắt) -> OTLP/HTTP span đến collector self-host
    (vd grafana/otel-lgtm). Air-gap: KHÔNG cấu hình endpoint -> chỉ metrics cục bộ.

Không cấu hình gì -> no-op (không phụ thuộc SaaS, đúng tinh thần chủ quyền dữ liệu).
"""
from __future__ import annotations

import logging

from app.config import get_settings

_log = logging.getLogger("bravo.obs")
_settings = get_settings()

# Prometheus counters/histograms cho LLM + tool (nhãn tối thiểu, không nhét PII).
try:
    from prometheus_client import Counter, Histogram

    LLM_CALLS = Counter("bravo_llm_calls_total", "Số lời gọi LLM", ["backend"])
    LLM_TOKENS = Counter("bravo_llm_tokens_total", "Token LLM (usage thật)", ["backend", "kind"])
    TOOL_CALLS = Counter("bravo_tool_calls_total", "Số lần gọi tool", ["tool", "status"])
    # F9: lượt truy hồi TRẢ VỀ RỖNG (lỗ corpus) — tín hiệu để đội corpus-ops bổ sung tài liệu.
    RETRIEVAL_ZERO_HITS = Counter("bravo_retrieval_zero_hits_total", "Số lượt truy hồi 0 kết quả")
    AGENT_TURN_SECONDS = Histogram("bravo_agent_turn_seconds", "Thời lượng một lượt agent")
    # Q7: thời gian tới TOKEN ĐẦU TIÊN (request -> event 'answer' đầu). Cổng chất lượng: p95 < 3s.
    FIRST_TOKEN_SECONDS = Histogram(
        "bravo_first_token_seconds", "Giây tới token trả lời đầu tiên",
        buckets=(0.5, 1, 1.5, 2, 3, 5, 8, 13))
    _PROM = True
except Exception:  # pragma: no cover - prometheus_client luôn có khi cài metrics
    _PROM = False


def record_llm(backend: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
    if _PROM and _settings.metrics_enabled:
        LLM_CALLS.labels(backend=backend).inc()
        if prompt_tokens:
            LLM_TOKENS.labels(backend=backend, kind="prompt").inc(prompt_tokens)
        if completion_tokens:
            LLM_TOKENS.labels(backend=backend, kind="completion").inc(completion_tokens)


def record_tool(tool: str, status: str) -> None:
    if _PROM and _settings.metrics_enabled:
        TOOL_CALLS.labels(tool=tool, status=status).inc()


def record_first_token(seconds: float) -> None:
    """Q7: ghi độ trễ tới token trả lời đầu tiên (đo tại tầng SSE). Best-effort."""
    if _PROM and _settings.metrics_enabled:
        try:
            FIRST_TOKEN_SECONDS.observe(max(0.0, seconds))
        except Exception:
            pass


def record_turn(seconds: float) -> None:
    """F5: ghi thời lượng một lượt agent (histogram trước đây định nghĩa nhưng không ai gọi)."""
    if _PROM and _settings.metrics_enabled:
        try:
            AGENT_TURN_SECONDS.observe(max(0.0, seconds))
        except Exception:
            pass


def record_zero_hit() -> None:
    """F9: đếm một lượt truy hồi trả về rỗng (tín hiệu lỗ corpus). Best-effort."""
    if _PROM and _settings.metrics_enabled:
        try:
            RETRIEVAL_ZERO_HITS.inc()
        except Exception:
            pass


def setup(app) -> None:
    """Gắn instrumentation vào FastAPI app (gọi một lần trong main). Fail-safe."""
    if _settings.metrics_enabled:
        try:
            from prometheus_fastapi_instrumentator import Instrumentator
            Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
            _log.info("Metrics: /metrics bật (Prometheus scrape).")
        except Exception as exc:  # noqa: BLE001
            _log.warning("Không bật được /metrics: %s", exc)

    if _settings.otel_exporter_endpoint:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider = TracerProvider(resource=Resource.create({"service.name": "bravo-ai-copilot"}))
            provider.add_span_processor(BatchSpanProcessor(
                OTLPSpanExporter(endpoint=_settings.otel_exporter_endpoint)))
            trace.set_tracer_provider(provider)
            FastAPIInstrumentor.instrument_app(app)
            _log.info("OTel: tracing -> %s", _settings.otel_exporter_endpoint)
        except Exception as exc:  # noqa: BLE001
            _log.warning("Không bật được OTel tracing: %s", exc)
