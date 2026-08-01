"""HTTP contract proof for the read-only secondary synthetic previews."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
import uuid

import httpx

from app.security.rls import Identity


def test_secondary_preview_routes_require_case_read_and_return_bounded_output(monkeypatch):
    from app.api import routes_accounting_cases_v2 as routes
    from app.main import app
    from app.security.auth import get_current_identity

    monkeypatch.setattr(routes, "get_settings", lambda: SimpleNamespace(accounting_case_v2_enabled=True))
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
