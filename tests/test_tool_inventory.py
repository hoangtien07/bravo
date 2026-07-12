"""Tool inventory + least-privilege audit gate (OWASP LLM06 / ASI03, Findings O #8)."""
from __future__ import annotations

import uuid

import pytest

from app.agent.loop import _register_builtin_tools
from app.agent.tool_inventory import audit_registry, describe_registry
from app.agent.tools import REGISTRY, Tool, call_tool
from app.security.rls import Identity


def test_builtin_registry_passes_least_privilege():
    _register_builtin_tools()
    report = audit_registry(REGISTRY)
    assert report.clean, report.errors


def test_inventory_describes_write_tool_as_validated_on_behalf_of():
    _register_builtin_tools()
    rows = {r.name: r for r in describe_registry(REGISTRY)}
    cje = rows["create_journal_entry"]
    assert cje.mode == "write->draft"
    assert cje.required_permission == "draft:create"
    assert cje.validated and cje.requires_approval and cje.on_behalf_of


def test_anonymous_write_is_flagged():
    reg = {"bad": Tool(name="bad", fn=lambda **k: k, read_only=False,
                       required_permission=None, payload_builder=lambda a: a)}
    report = audit_registry(reg)
    assert any("anonymous write" in e for e in report.errors)


def test_unvalidated_write_is_flagged():
    reg = {"raw": Tool(name="raw", fn=lambda **k: k, read_only=False,
                       required_permission="draft:create")}  # no payload_builder
    report = audit_registry(reg)
    assert any("unvalidated" in e for e in report.errors)


def test_malformed_permission_warns():
    reg = {"r": Tool(name="r", fn=lambda **k: k, read_only=True,
                     required_permission="metricread")}  # missing ':'
    report = audit_registry(reg)
    assert report.clean  # warning only, not an error
    assert any("resource:action" in w for w in report.warnings)


def test_open_read_tool_without_identity_is_flagged():
    """T3-lite: an open read tool that doesn't take `identity` may bypass RLS -> error."""
    bad = {"leaky": Tool(name="leaky", fn=lambda q: q, read_only=True)}  # no perm, no identity
    assert any("bypass RLS" in e for e in audit_registry(bad).errors)
    # A read tool that DOES consume identity is fine (kb_search shape).
    ok = {"safe": Tool(name="safe", fn=lambda q, *, identity, db=None: q, read_only=True)}
    assert audit_registry(ok).clean


@pytest.mark.asyncio
async def test_llm_cannot_escalate_identity_via_args():
    """On-behalf-of: a tool always runs under the CALLER identity, even if the LLM injects
    its own `identity`/`db` in the tool args (it cannot see them in the schema, but defense)."""
    seen = {}

    def probe(identity: Identity, **kw):
        seen["employee_id"] = identity.employee_id
        return "ok"

    REGISTRY["_probe_ident"] = Tool(name="_probe_ident", fn=probe, read_only=True)
    try:
        caller = Identity(employee_id=uuid.uuid4(), is_admin=True)
        forged = uuid.uuid4()
        out = await call_tool("_probe_ident", {"identity": {"employee_id": str(forged)}}, caller)
        assert out.get("status") == "ok"
        assert seen["employee_id"] == caller.employee_id  # forged identity ignored
        assert seen["employee_id"] != forged
    finally:
        REGISTRY.pop("_probe_ident", None)
