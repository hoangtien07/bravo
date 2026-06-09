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


async def chat(messages: list[dict], *, sensitive: bool | None = None,
               allow_cloud_task: bool = False, **kwargs) -> tuple[str, RoutingDecision]:
    """Route a chat completion. Returns (text, decision). Audit `decision` on egress."""
    d = decide(sensitive, allow_cloud_task)
    client = _cloud if d.backend == "cloud" else _local
    resp = await client.chat.completions.create(model=d.model, messages=messages, **kwargs)
    return resp.choices[0].message.content or "", d
