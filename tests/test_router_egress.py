"""WP-C / seam 1 — router audit-then-egress + context-driven sensitivity (ADR-0011)."""
from __future__ import annotations

import pytest

from app.llm import router
from app.llm.router import RoutingDecision, _audit_egress


class _FakeResp:
    class _Choice:
        class _Msg:
            content = "ok"
        message = _Msg()
    choices = [_Choice()]


class _FakeClient:
    class chat:
        class completions:
            @staticmethod
            async def create(**kw):
                return _FakeResp()


class _FakeDB:
    def __init__(self):
        self.added = []

    def add(self, o):
        self.added.append(o)

    async def commit(self):
        pass


@pytest.mark.asyncio
async def test_sensitive_context_forces_local(monkeypatch):
    """A context item tagged sensitive (payroll) -> classify_context -> backend LOCAL."""
    monkeypatch.setattr(router, "_local", _FakeClient())
    sens = type("X", (), {"department_ids": [], "knowledge_type": "payroll"})()
    text, d = await router.chat([{"role": "user", "content": "x"}], context=[sens], db=None)
    assert d.backend == "local"
    assert text == "ok"


@pytest.mark.asyncio
async def test_nonsensitive_demo_metric_not_forced_local_by_context(monkeypatch):
    """A demo (is_demo) metric item is non-sensitive -> classify returns False (cloud-eligible)."""
    from app.security.sensitivity import classify_context
    demo = type("M", (), {"metric_id": "x", "currency": "VND", "is_demo": True,
                          "department_ids": []})()
    assert classify_context([demo]) is False  # cloud-eligible (sovereignty: demo mock only)


@pytest.mark.asyncio
async def test_audit_then_egress_writes_auditlog_before_call():
    """_audit_egress records an llm.egress AuditLog with a prompt hash (no raw prompt)."""
    db = _FakeDB()
    await _audit_egress(db, RoutingDecision("cloud", "gpt-x", "r"),
                        [{"role": "user", "content": "bí mật"}])
    egress = [o for o in db.added if getattr(o, "action", None) == "llm.egress"]
    assert len(egress) == 1
    assert "prompt_hash" in egress[0].detail and "bí mật" not in str(egress[0].detail)


@pytest.mark.asyncio
async def test_audit_egress_noop_without_db():
    # db=None (unit context) -> no crash, no audit.
    await _audit_egress(None, RoutingDecision("cloud", "m", "r"), [{"role": "user", "content": "x"}])


# --------------------------------------------------------------------------------------
# Structured-output plumbing: local backend format phải theo local_structured_mode.
# Regression: demo trỏ "local" -> OpenAI KHÔNG chấp nhận guided_json (lỗi 400).
# --------------------------------------------------------------------------------------
def test_structured_kwargs_local_mode(monkeypatch):
    from app.llm.router import _settings, _structured_kwargs

    schema = {"type": "object"}
    monkeypatch.setattr(_settings, "structured_output", True)
    cloud = RoutingDecision("cloud", "gpt-4o", "x")
    local = RoutingDecision("local", "qwen", "x")

    # cloud luôn json_object (OpenAI-compatible rộng rãi)
    assert _structured_kwargs(cloud, schema) == {"response_format": {"type": "json_object"}}

    # local=guided_json -> vLLM guided decoding (mặc định production)
    monkeypatch.setattr(_settings, "local_structured_mode", "guided_json")
    assert _structured_kwargs(local, schema) == {"extra_body": {"guided_json": schema}}

    # local=json_object -> KHÔNG gửi guided_json (endpoint OpenAI-compatible như demo)
    monkeypatch.setattr(_settings, "local_structured_mode", "json_object")
    assert _structured_kwargs(local, schema) == {"response_format": {"type": "json_object"}}

    # off -> không ép
    monkeypatch.setattr(_settings, "local_structured_mode", "off")
    assert _structured_kwargs(local, schema) == {}

    # tắt structured_output -> luôn rỗng
    monkeypatch.setattr(_settings, "structured_output", False)
    assert _structured_kwargs(cloud, schema) == {}


# --------------------------------------------------------------------------------------
# ADR-0019 cloud-only egress policy: no local backend -> every call routes cloud, even
# sensitive context (the egress AUDIT stays as the compliance artifact, not a block).
# --------------------------------------------------------------------------------------
def test_cloud_only_policy_routes_cloud_even_when_sensitive(monkeypatch):
    from app.llm.router import _settings, decide
    monkeypatch.setattr(_settings, "egress_policy", "cloud_only")
    monkeypatch.setattr(_settings, "cloud_model", "gpt-4o")
    monkeypatch.setattr(router, "_cloud", _FakeClient())  # cloud client present
    assert decide(sensitive=True).backend == "cloud"
    assert decide(sensitive=None).backend == "cloud"


def test_hybrid_policy_still_fails_closed_to_local(monkeypatch):
    from app.llm.router import _settings, decide
    monkeypatch.setattr(_settings, "egress_policy", "hybrid")
    monkeypatch.setattr(router, "_cloud", _FakeClient())
    assert decide(sensitive=True).backend == "local"        # sensitive pinned local
    assert decide(sensitive=None).backend == "local"        # unknown -> fail-closed
