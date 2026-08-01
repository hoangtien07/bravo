"""HTTP contract proof for the read-only secondary synthetic previews."""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
import uuid

import httpx
import pytest

from app.security.rls import Identity


def test_secondary_preview_routes_require_case_read_and_return_bounded_output(monkeypatch):
    from app.api import routes_accounting_cases_v2 as routes
    from app.main import app
    from app.security.auth import get_current_identity

    monkeypatch.setattr(routes, "get_settings", lambda: SimpleNamespace(
        accounting_case_v2_enabled=True,
        accounting_case_v2_demo_config="file_system/core_v2_synthetic_demo.yaml",
    ))
    allowed = Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                       permissions=frozenset({"accounting_case:read:own_dept"}))

    async def identity():
        return allowed

    async def run() -> None:
        app.dependency_overrides[get_current_identity] = identity
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                voucher = await client.post("/api/v2/accounting-cases/preview/voucher-review", json={
                    "invoice_total": "110", "invoice_tax": "10", "invoice_net": "100",
                    "po_amount": "110", "received": True, "bravo_document_id": "synthetic-draft-1",
                })
                assert voucher.status_code == 200, voucher.text
                assert {item["status"] for item in voucher.json()} == {"pass"}
                close = await client.post("/api/v2/accounting-cases/preview/period-close-readiness", json={
                    "prerequisites": [{"prerequisite_id": "bank", "required": True, "status": "pending", "evidence_fresh": True}],
                    "reconciliations": [],
                })
                assert close.status_code == 200, close.text
                assert close.json()["ready"] is False
                assert "did not execute" in close.json()["execution"]
        finally:
            app.dependency_overrides.pop(get_current_identity, None)

    asyncio.run(run())


@pytest.mark.parametrize(
    ("capability", "guard_name"),
    (("voucher_review", "_require_voucher_preview"), ("period_close_readiness", "_require_period_close_preview")),
)
def test_secondary_preview_capability_flag_is_a_route_backstop(monkeypatch, tmp_path, capability, guard_name):
    from fastapi import HTTPException

    from app.api import routes_accounting_cases_v2 as routes

    disabled = tmp_path / f"disabled-{capability}.yaml"
    source = Path("file_system/core_v2_synthetic_demo.yaml").read_text(encoding="utf-8")
    disabled.write_text(source.replace(f"{capability}: true", f"{capability}: false"), encoding="utf-8")
    monkeypatch.setattr(routes, "get_settings", lambda: SimpleNamespace(
        accounting_case_v2_enabled=True,
        accounting_case_v2_demo_config=str(disabled),
    ))

    with pytest.raises(HTTPException) as raised:
        getattr(routes, guard_name)()
    assert raised.value.status_code == 404
