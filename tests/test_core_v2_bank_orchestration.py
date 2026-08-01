from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace

import httpx
import pytest

from app.core_v2.bank_orchestration import CaseAccessError, SyntheticBankCaseService
from app.core_v2.case_state import CaseStateError, IdempotencyConflict, RevisionConflict
from app.core_v2.contracts import CaseActor, CaseState
from app.security.rls import Identity
from tests.db_support import db_available


_DEPT_A = frozenset({"dept-a"})
_DEPT_B = frozenset({"dept-b"})


def _actor(user_id: str, role: str = "preparer") -> CaseActor:
    return CaseActor(user_id=user_id, role=role, scope_ref="dept-a" if role != "admin" else "admin")


def _prepared(service: SyntheticBankCaseService):
    maker = _actor("maker")
    case = service.create(actor=maker, scope=service.evidence.scope, department_ids=_DEPT_A, idempotency_key="create")
    case = service.attach_evidence(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                                   expected_revision=case.revision, idempotency_key="evidence")
    return maker, case


def test_headless_bank_case_completes_with_fixture_evidence_and_no_llm_or_bravo_api():
    service = SyntheticBankCaseService()
    maker, case = _prepared(service)
    case = service.run_checks(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                              expected_revision=case.revision, idempotency_key="checks")
    assert case.state is CaseState.NEEDS_REVIEW
    view = service.view(case)
    assert len(view["results"]) == 7
    assert view["trace"]["raw_evidence_retained"] is False

    checker = _actor("checker", "reviewer")
    dispositions = {item["finding_id"]: "investigate" for item in view["findings"]}
    case = service.review(case.case_id.value, actor=checker, department_ids=_DEPT_A,
                          expected_revision=case.revision, idempotency_key="review", dispositions=dispositions,
                          payload_hash_value=view["draft_payload_hash"], evidence_hash=view["evidence_hash"],
                          result_hash=view["result_hash"])
    reviewed = service.view(case)
    case, artifact = service.export(case.case_id.value, actor=checker, department_ids=_DEPT_A,
                                    expected_revision=case.revision, idempotency_key="export",
                                    payload_hash_value=reviewed["draft_payload_hash"], evidence_hash=reviewed["evidence_hash"],
                                    review_hash=reviewed["approval"]["review_hash"])
    assert case.state is CaseState.EXPORTED
    assert artifact["status"] == "artifact_produced_not_executed"
    assert artifact["execution"] == "artifact produced; BRAVO did not execute anything."
    assert artifact["payload_hash"]


def test_scope_authorization_idempotency_and_revision_conflicts_fail_closed():
    service = SyntheticBankCaseService()
    maker, case = _prepared(service)
    with pytest.raises(CaseAccessError):
        service.get(case.case_id.value, actor=_actor("other"), department_ids=_DEPT_B)
    retry = service.attach_evidence(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                                    expected_revision=case.revision - 2, idempotency_key="evidence")
    assert retry == case
    with pytest.raises(RevisionConflict):
        service.run_checks(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                           expected_revision=case.revision - 1, idempotency_key="stale")


def test_maker_cannot_review_and_fixture_scope_cannot_be_substituted():
    service = SyntheticBankCaseService()
    maker, case = _prepared(service)
    case = service.run_checks(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                              expected_revision=case.revision, idempotency_key="checks")
    with pytest.raises(CaseAccessError):
        service.review(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                       expected_revision=case.revision, idempotency_key="review", dispositions={},
                       payload_hash_value="a" * 64, evidence_hash="a" * 64, result_hash="a" * 64)
    foreign_scope = service.evidence.scope.model_copy(update={"tenant_id": "other"})
    with pytest.raises(CaseAccessError, match="frozen synthetic"):
        service.create(actor=maker, scope=foreign_scope, department_ids=_DEPT_A, idempotency_key="other-fixture")


def test_cross_operation_key_and_failed_review_retry_cannot_mutate_state():
    service = SyntheticBankCaseService()
    maker, case = _prepared(service)
    with pytest.raises(IdempotencyConflict):
        service.run_checks(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                           expected_revision=case.revision, idempotency_key="evidence")

    case = service.run_checks(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                              expected_revision=case.revision, idempotency_key="checks")
    before = service.view(case)
    checker = _actor("checker", "reviewer")
    dispositions = {item["finding_id"]: "investigate" for item in before["findings"]}
    case = service.review(case.case_id.value, actor=checker, department_ids=_DEPT_A,
                          expected_revision=case.revision, idempotency_key="review", dispositions=dispositions,
                          payload_hash_value=before["draft_payload_hash"], evidence_hash=before["evidence_hash"],
                          result_hash=before["result_hash"])
    after = service.view(case)
    tampered = {item["finding_id"]: "resolved" for item in before["findings"]}
    with pytest.raises(IdempotencyConflict):
        service.review(case.case_id.value, actor=checker, department_ids=_DEPT_A,
                       expected_revision=case.revision, idempotency_key="review", dispositions=tampered,
                       payload_hash_value=after["draft_payload_hash"], evidence_hash=after["evidence_hash"],
                       result_hash=after["result_hash"])
    assert service.view(case)["review_dispositions"] == dispositions


def test_evidence_supersession_invalidates_draft_review_and_forces_fresh_checks():
    service = SyntheticBankCaseService()
    maker, case = _prepared(service)
    case = service.run_checks(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                              expected_revision=case.revision, idempotency_key="checks")
    assert service.view(case)["draft_payload_hash"]
    case = service.supersede_evidence(case.case_id.value, actor=maker, department_ids=_DEPT_A,
                                      expected_revision=case.revision, idempotency_key="replace-bank",
                                      source_type="bank_statement")
    view = service.view(case)
    assert case.state is CaseState.EVIDENCE_READY
    assert view["results"] == [] and view["findings"] == []
    assert view["draft_payload_hash"] is None and view["approval"] is None
    with pytest.raises(CaseStateError):
        service.export(case.case_id.value, actor=_actor("checker", "reviewer"), department_ids=_DEPT_A,
                       expected_revision=case.revision, idempotency_key="export-after-replace",
                       payload_hash_value="a" * 64, evidence_hash="a" * 64, review_hash="a" * 64)


@pytest.mark.skipif(not db_available(), reason="Postgres not reachable")
def test_http_routes_enforce_server_identity_scope_and_complete_headlessly(monkeypatch):
    from app.api import routes_accounting_cases_v2 as routes
    from app.main import app
    from app.security.auth import get_current_identity

    service = SyntheticBankCaseService()
    routes._service = service
    monkeypatch.setattr(routes, "get_settings", lambda: SimpleNamespace(accounting_case_v2_enabled=True))
    identity = Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                        permissions=frozenset({"accounting_case:create:own_dept"}))

    async def override_identity():
        return identity

    async def run():
        app.dependency_overrides[get_current_identity] = override_identity
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                create = await client.post("/api/v2/accounting-cases", json={
                    "scope": service.evidence.scope.model_dump(mode="json"), "idempotency_key": "create-http",
                })
                assert create.status_code == 201, create.text
                case = create.json()
                case_id = case["case_id"]
                foreign = Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()], permissions=frozenset())

                async def foreign_identity():
                    return foreign

                app.dependency_overrides[get_current_identity] = foreign_identity
                denied = await client.get(f"/api/v2/accounting-cases/{case_id}")
                assert denied.status_code == 403
                app.dependency_overrides[get_current_identity] = override_identity
                evidence = await client.post(f"/api/v2/accounting-cases/{case_id}/evidence", json={
                    "expected_revision": case["revision"], "idempotency_key": "evidence-http",
                })
                assert evidence.status_code == 200, evidence.text
                checks = await client.post(f"/api/v2/accounting-cases/{case_id}/run-checks", json={
                    "expected_revision": evidence.json()["revision"], "idempotency_key": "checks-http",
                })
                assert checks.status_code == 200, checks.text
        finally:
            app.dependency_overrides.pop(get_current_identity, None)

    asyncio.run(run())
