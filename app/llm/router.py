"""Model Router (LLM Gateway) — ADR-0003 hybrid + SECURITY-RLS §9 data-egress.

EVERY LLM call goes through here. Router picks local vs cloud based on:
deployment config (cloud on/off) + sensitivity of the context + task. Default LOCAL.
FAIL-CLOSED: if sensitivity is unknown OR cloud disabled OR any context is sensitive
→ run LOCAL. Sensitive data (accounting/HR/PII) is pinned local and never egresses.

`chat()` = buffered completion (returns text + decision carrying REAL token usage).
`chat_stream()` = token streaming primitive (yields real deltas from the model, then a
final usage event). Both preserve audit-then-egress (ADR-0011): the cloud egress is
audited BEFORE the request opens.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import get_settings

_settings = get_settings()

# GPU on-prem chịu được ~1-2 stream đồng thời (W2.3). Semaphore chặn quá tải -> request thứ
# N+1 CHỜ (không treo GPU). Áp cho cả chat lẫn chat_stream. max<=0 -> không giới hạn.
_llm_sema = asyncio.Semaphore(max(1, _settings.llm_max_concurrency))

# timeout/max_retries: một lời gọi đi lạc (vd fail-closed về local nhưng KHÔNG có LLM local)
# phải FAIL NHANH + rõ, thay vì treo (mặc định client ~10 phút) khiến UI "không có response".
_local = AsyncOpenAI(base_url=_settings.llm_local_base_url, api_key=_settings.llm_local_api_key,
                     timeout=30.0, max_retries=2)
_cloud = (
    AsyncOpenAI(base_url=_settings.cloud_base_url or None, api_key=_settings.cloud_api_key,
                timeout=30.0, max_retries=2)
    if _settings.cloud_enabled and _settings.cloud_api_key
    else None
)


class VisionUnsupportedError(RuntimeError):
    """Raised when a turn carries an image but the routed model can't accept images (RC-BE1).
    Its message is user-safe (no internal detail) and is surfaced verbatim by the SSE error path."""


def _messages_have_image(messages: list[dict]) -> bool:
    """True if any message content is a multimodal array containing an image_url part."""
    for m in messages:
        content = m.get("content")
        if isinstance(content, list):
            if any(isinstance(p, dict) and p.get("type") == "image_url" for p in content):
                return True
    return False


def _slot_supports_vision(backend: str) -> bool:
    return _settings.cloud_vision if backend == "cloud" else _settings.llm_local_vision


def _guard_vision(d: RoutingDecision, messages: list[dict]) -> None:
    """Fail LOUD if the turn has an image but the routed slot is text-only. Prevents the model
    from silently 'answering blind' about an image it cannot see (the user's original bug class)."""
    if _messages_have_image(messages) and not _slot_supports_vision(d.backend):
        raise VisionUnsupportedError(
            "Ảnh bạn gửi không xử lý được vì mô hình hiện tại không đọc ảnh. "
            "Vui lòng bật mô hình hỗ trợ ảnh (vision) hoặc mô tả nội dung ảnh bằng chữ.")


@dataclass
class RoutingDecision:
    backend: str  # "local" | "cloud"
    model: str
    reason: str
    # Token usage THẬT từ response (W1.2). 0 nếu backend không trả usage (một số vLLM/Ollama
    # cũ) -> caller có thể ước lượng thay thế. total_tokens dùng cho budget + cost-tracking.
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def decide(sensitive: bool | None, allow_cloud_task: bool = False) -> RoutingDecision:
    """Choose backend. Fail-closed to local — EXCEPT under egress_policy=cloud_only (ADR-0019),
    where no local backend exists and every call routes cloud (egress still audited)."""
    if _settings.egress_policy == "cloud_only" and _cloud is not None:
        return RoutingDecision("cloud", _settings.cloud_model, "cloud-only policy (ADR-0019)")
    if not _settings.cloud_enabled or _cloud is None:
        return RoutingDecision("local", _settings.llm_local_model, "cloud disabled")
    if sensitive is None:
        return RoutingDecision("local", _settings.llm_local_model, "sensitivity unknown (fail-closed)")
    if sensitive:
        return RoutingDecision("local", _settings.llm_local_model, "sensitive data pinned local")
    if not allow_cloud_task:
        return RoutingDecision("local", _settings.llm_local_model, "task not whitelisted for cloud")
    return RoutingDecision("cloud", _settings.cloud_model, "non-sensitive + cloud allowed")


async def _audit_egress(db, d: RoutingDecision, messages: list[dict]) -> None:
    """Audit-then-egress (ADR-0011 / WP-C): ghi AuditLog TRƯỚC khi prompt rời mạng ra cloud.

    Nếu ghi audit lỗi -> raise (db.commit propagate) -> KHÔNG egress (fail-closed). db=None
    (vd unit-test) -> bỏ qua. prompt_hash để truy vết, không lưu nội dung thô.
    """
    if db is None:
        return
    import hashlib
    import json as _json

    from app.database.models import AuditLog

    # Replace multimodal image payloads with their own sha256 so we hash a compact digest,
    # not megabytes of base64 (Track 3). The audit still uniquely fingerprints the prompt.
    def _lean(messages: list[dict]) -> list[dict]:
        out = []
        for m in messages:
            content = m.get("content")
            if isinstance(content, list):
                parts = []
                for p in content:
                    if isinstance(p, dict) and p.get("type") == "image_url":
                        url = (p.get("image_url") or {}).get("url", "")
                        parts.append({"type": "image_url",
                                      "sha256": hashlib.sha256(url.encode()).hexdigest()})
                    else:
                        parts.append(p)
                out.append({**m, "content": parts})
            else:
                out.append(m)
        return out

    prompt_hash = hashlib.sha256(
        _json.dumps(_lean(messages), ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    db.add(AuditLog(action="llm.egress",
                    detail={"provider": d.backend, "model": d.model, "prompt_hash": prompt_hash}))
    await db.commit()


def _classify(sensitive: bool | None, context: list | None) -> bool | None:
    """WP-C: nếu caller không truyền `sensitive` nhưng có `context`, tự phân loại (fail-closed)."""
    if sensitive is None and context is not None:
        from app.security.sensitivity import classify_context
        return classify_context(context)
    return sensitive


def _structured_kwargs(d: RoutingDecision, schema: dict | None) -> dict:
    """Structured-output plumbing (W1.3). Trả kwargs bơm vào completions.create theo backend.

    - cloud (OpenAI-compatible): response_format json_object (được hỗ trợ rộng; prompt đã yêu
      cầu 'chỉ JSON'). json_schema strict không phải endpoint nào cũng chịu -> dùng json_object.
    - local: theo settings.local_structured_mode — 'guided_json' (vLLM/outlines, ép schema, mạnh
      nhất) | 'json_object' (khi "local" thực chất là endpoint OpenAI-compatible, vd demo trỏ
      OpenAI: guided_json bị OpenAI từ chối 400) | 'off'. Tắt chung bằng structured_output=False.
    """
    if schema is None or not _settings.structured_output:
        return {}
    if d.backend == "cloud":
        return {"response_format": {"type": "json_object"}}
    mode = _settings.local_structured_mode
    if mode == "off":
        return {}
    if mode == "json_object":
        return {"response_format": {"type": "json_object"}}
    return {"extra_body": {"guided_json": schema}}   # 'guided_json' (vLLM) — mặc định


async def chat(messages: list[dict], *, context: list | None = None,
               sensitive: bool | None = None, allow_cloud_task: bool = False,
               json_schema: dict | None = None, db=None, **kwargs) -> tuple[str, RoutingDecision]:
    """Route a chat completion. Returns (text, decision) — decision carries REAL token usage.

    `json_schema` bật structured output (json_object cloud / guided_json vLLM). Router tự phân
    loại độ nhạy từ `context` (fail-closed → local). Cloud egress được audit TRƯỚC khi gọi.
    """
    sensitive = _classify(sensitive, context)
    d = decide(sensitive, allow_cloud_task)
    _guard_vision(d, messages)                 # RC-BE1: fail loud before any blind image answer
    client = _cloud if d.backend == "cloud" else _local
    if d.backend == "cloud":
        await _audit_egress(db, d, messages)  # fail-closed: audit trước, lỗi audit -> không egress
    kwargs.update(_structured_kwargs(d, json_schema))
    async with _llm_sema:
        resp = await client.chat.completions.create(model=d.model, messages=messages, **kwargs)
    _apply_usage(d, getattr(resp, "usage", None))
    _record_metrics(d)
    return resp.choices[0].message.content or "", d


async def chat_stream(messages: list[dict], *, context: list | None = None,
                      sensitive: bool | None = None, allow_cloud_task: bool = False,
                      json_schema: dict | None = None, db=None, **kwargs) -> AsyncIterator[dict]:
    """Token-streaming primitive (W1.1). Yields REAL deltas from the model:

        {"type": "delta", "text": "..."}          # nhiều event, token thật
        {"type": "done", "decision": RoutingDecision, "text": "<full>"}   # 1 event cuối

    Giữ audit-then-egress: cloud egress audit TRƯỚC khi mở stream. include_usage=True để lấy
    token usage THẬT ở chunk cuối (OpenAI-compatible + vLLM hỗ trợ). `json_schema` bật
    structured output (json_object cloud / guided_json vLLM) — dùng cho single-generation
    decide-answer streaming (P0b): model stream một object JSON hợp lệ, caller parse tăng dần.
    """
    sensitive = _classify(sensitive, context)
    d = decide(sensitive, allow_cloud_task)
    _guard_vision(d, messages)                 # RC-BE1: fail loud before any blind image answer
    client = _cloud if d.backend == "cloud" else _local
    if d.backend == "cloud":
        await _audit_egress(db, d, messages)
    kwargs.update(_structured_kwargs(d, json_schema))
    async with _llm_sema:
        stream = await client.chat.completions.create(
            model=d.model, messages=messages, stream=True,
            stream_options={"include_usage": True}, **kwargs)
        parts: list[str] = []
        async for chunk in stream:
            if getattr(chunk, "usage", None):
                _apply_usage(d, chunk.usage)
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0].delta, "content", None) if choices[0].delta else None
            if delta:
                parts.append(delta)
                yield {"type": "delta", "text": delta}
    _record_metrics(d)
    yield {"type": "done", "decision": d, "text": "".join(parts)}


def _apply_usage(d: RoutingDecision, usage) -> None:
    if not usage:
        return
    d.prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    d.completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    d.total_tokens = int(getattr(usage, "total_tokens", 0)
                         or (d.prompt_tokens + d.completion_tokens))


def _record_metrics(d: RoutingDecision) -> None:
    """Ghi Prometheus counter (W2.2) — best-effort, không làm vỡ lời gọi."""
    try:
        from app.observability import record_llm
        record_llm(d.backend, d.prompt_tokens, d.completion_tokens)
    except Exception:
        pass
