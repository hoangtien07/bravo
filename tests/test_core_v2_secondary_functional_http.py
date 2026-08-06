"""Local HTTP/DB proof for the two BF-02/BF-03 functional AccountingCases."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
import uuid

import httpx
import pytest

from app.core_v2.contracts import CaseType
from app.core_v2.period_close_orchestration import SyntheticPeriodCloseCaseService
from app.core_v2.voucher_orchestration import SyntheticVoucherCaseService
from app.security.rls import Identity
from tests.db_support import db_available


@pytest.mark.skipif(not db_available(), reason="Postgres not reachable")
@pytest.mark.parametrize(
    ("case_type", "service_type", "execution_text"),
    [
        (CaseType.VOUCHER_EVIDENCE_REVIEW, SyntheticVoucherCaseService, "did not create, post, or change a voucher"),
        (CaseType.PERIOD_CLOSE_READINESS, SyntheticPeriodCloseCaseService, "did not execute close"),
    ],
)
def test_secondary_case_completes_durable_http_db_flow(monkeypatch, case_type, service_type, execution_text):
    from app.api import routes_accounting_cases_v2 as routes
    from app.database import async_session_factory, engine
    from app.database.models import Department, Employee, EmployeeDepartment
    from app.main import app
    from app.security.auth import get_current_identity

    service = service_type()
    department_id = uuid.uuid4()
    maker = Identity(
        employee_id=uuid.uuid4(),
        department_ids=[department_id],
        permissions=frozenset({"accounting_case:create:own_dept", "accounting_case:read:own_dept"}),
    )
    reviewer = Identity(
        employee_id=uuid.uuid4(),
        department_ids=[department_id],
        permissions=frozenset({"accounting_case:review:own_dept", "accounting_case:read:own_dept"}),
    )
    monkeypatch.setattr(routes, "get_settings", lambda: SimpleNamespace(
        accounting_case_v2_enabled=True,
        accounting_case_v2_demo_config="file_system/core_v2_synthetic_demo.yaml",
    ))

    async def maker_identity():
        return maker

    async def reviewer_identity():
        return reviewer

    async def run():
        async with async_session_factory() as db:
            db.add(Department(id=department_id, name=f"secondary-case-test-{department_id}"))
            for identity, label in ((maker, "Maker"), (reviewer, "Reviewer")):
                db.add(Employee(id=identity.employee_id, email=f"secondary-{identity.employee_id}@example.invalid",
                                full_name=label, password_hash="test", permissions=list(identity.permissions)))
            await db.flush()
            for identity in (maker, reviewer):
                db.add(EmployeeDepartment(employee_id=identity.employee_id, department_id=department_id))
            await db.commit()
        app.dependency_overrides[get_current_identity] = maker_identity
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                created = await client.post("/api/v2/accounting-cases", json={
                    "case_type": case_type.value,
                    "scope": service.evidence.scope.model_dump(mode="json"),
                    "idempotency_key": f"{case_type.value}-create-{uuid.uuid4().hex}",
                })
                assert created.status_code == 201, created.text
                case = created.json()
                case_id = case["case_id"]

                evidence = await client.post(f"/api/v2/accounting-cases/{case_id}/evidence", json={
                    "expected_revision": case["revision"], "idempotency_key": f"{case_type.value}-evidence-{uuid.uuid4().hex}",
                })
                assert evidence.status_code == 200, evidence.text
                checked = await client.post(f"/api/v2/accounting-cases/{case_id}/run-checks", json={
                    "expected_revision": evidence.json()["revision"], "idempotency_key": f"{case_type.value}-checks-{uuid.uuid4().hex}",
                })
                assert checked.status_code == 200, checked.text
                checked_case = checked.json()
                assert checked_case["state"] == "NEEDS_REVIEW"

                app.dependency_overrides[get_current_identity] = reviewer_identity
                reviewed = await client.post(f"/api/v2/accounting-cases/{case_id}/review", json={
                    "expected_revision": checked_case["revision"], "idempotency_key": f"{case_type.value}-review-{uuid.uuid4().hex}",
                    "decisions": [], "payload_hash": checked_case["draft_payload_hash"],
                    "evidence_hash": checked_case["evidence_hash"], "result_hash": checked_case["result_hash"],
                })
                assert reviewed.status_code == 200, reviewed.text
                reviewed_case = reviewed.json()
                exported = await client.post(f"/api/v2/accounting-cases/{case_id}/export", json={
                    "expected_revision": reviewed_case["revision"], "idempotency_key": f"{case_type.value}-export-{uuid.uuid4().hex}",
                    "payload_hash": reviewed_case["draft_payload_hash"], "evidence_hash": reviewed_case["evidence_hash"],
                    "review_hash": reviewed_case["approval"]["review_hash"],
                })
                assert exported.status_code == 200, exported.text
                assert exported.json()["case"]["state"] == "EXPORTED"
                assert execution_text in exported.json()["artifact"]["execution"]
        finally:
            app.dependency_overrides.pop(get_current_identity, None)
            await engine.dispose()

    asyncio.run(run())
