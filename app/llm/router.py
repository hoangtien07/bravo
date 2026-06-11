"""Model Router (LLM Gateway) — ADR-0003 hybrid + SECURITY-RLS §9 data-egress.

EVERY LLM call goes through here. Router picks local vs cloud based on:
deployment config (cloud on/off) + sensitivity of the context + task. Default LOCAL.
FAIL-CLOSED: if sensitivity is unknown OR cloud disabled OR any context is sensitive
→ run LOCAL. Sensitive data (accounting/HR/PII) is pinned local and never egresses.
"""
from __future__ import annotations

from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import get_settings

_settings = get_settings()

_local = AsyncOpenAI(base_url=_settings.llm_local_base_url, api_key=_settings.llm_local_api_key)
_cloud = (
    AsyncOpenAI(base_url=_settings.cloud_base_url or None, api_key=_settings.cloud_api_key)
    if _settings.cloud_enabled and _settings.cloud_api_key
    else None
)


@dataclass
class RoutingDecision:
    backend: str  # "local" | "cloud"
    model: str
    reason: str


def decide(sensitive: bool | None, allow_cloud_task: bool = False) -> RoutingDecision:
    """Choose backend. Fail-closed to local."""
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

    prompt_hash = hashlib.sha256(
        _json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    db.add(AuditLog(action="llm.egress",
                    detail={"provider": d.backend, "model": d.model, "prompt_hash": prompt_hash}))
    await db.commit()


async def chat(messages: list[dict], *, context: list | None = None,
               sensitive: bool | None = None, allow_cloud_task: bool = False,
               db=None, **kwargs) -> tuple[str, RoutingDecision]:
    """Route a chat completion. Returns (text, decision).

    WP-C: nếu caller KHÔNG truyền `sensitive` nhưng có `context` (chunks + metric-results),
    router TỰ phân loại độ nhạy (fail-closed) — không tin tham số thủ công. Mọi lời gọi cloud
    được audit TRƯỚC khi gọi (audit-then-egress).
    """
    if sensitive is None and context is not None:
        from app.security.sensitivity import classify_context
        sensitive = classify_context(context)
    d = decide(sensitive, allow_cloud_task)
    client = _cloud if d.backend == "cloud" else _local
    if d.backend == "cloud":
        await _audit_egress(db, d, messages)  # fail-closed: audit trước, lỗi audit -> không egress
    resp = await client.chat.completions.create(model=d.model, messages=messages, **kwargs)
    return resp.choices[0].message.content or "", d
