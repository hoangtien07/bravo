import pytest

from app.core_v2.bank_orchestration import CaseAccessError
from app.core_v2.case_state import CaseStateError
from app.core_v2.contracts import CaseActor, CaseState
from app.core_v2.period_close_orchestration import SyntheticPeriodCloseCaseService


_DEPTS = frozenset({"dept-a"})


def _actor(user_id: str, role: str = "preparer") -> CaseActor:
    return CaseActor(user_id=user_id, role=role, scope_ref="dept-a")


def test_period_close_server_policy_completes_functional_lifecycle_without_client_prerequisites():
    service = SyntheticPeriodCloseCaseService()
    maker = _actor("maker")
    case = service.create(actor=maker, scope=service.evidence.scope, department_ids=_DEPTS, idempotency_key="create")
    case = service.attach_evidence(case.case_id.value, actor=maker, department_ids=_DEPTS,
                                   expected_revision=case.revision, idempotency_key="evidence")
    case = service.run_checks(case.case_id.value, actor=maker, department_ids=_DEPTS,
                              expected_revision=case.revision, idempotency_key="checks")
    assert case.state is CaseState.NEEDS_REVIEW
    view = service.view(case)
    assert {item["result"]["status"] for item in view["results"]} == {"pass"}
    assert case.draft_action is not None and case.draft_action.payload["ready"] is True

    reviewer = _actor("checker", "reviewer")
    case = service.review(case.case_id.value, actor=reviewer, department_ids=_DEPTS,
                          expected_revision=case.revision, idempotency_key="review", decisions=(),
                          payload_hash_value=view["draft_payload_hash"], evidence_hash=view["evidence_hash"],
                          result_hash=view["result_hash"])
    reviewed = service.view(case)
    case, artifact = service.export(case.case_id.value, actor=reviewer, department_ids=_DEPTS,
                                    expected_revision=case.revision, idempotency_key="export",
                                    payload_hash_value=reviewed["draft_payload_hash"], evidence_hash=reviewed["evidence_hash"],
                                    review_hash=reviewed["approval"]["review_hash"])
    assert case.state is CaseState.EXPORTED
    assert artifact["ready"] is True
    assert "did not execute close" in artifact["execution"]


def test_period_close_rejects_foreign_scope_and_client_source_type():
    service = SyntheticPeriodCloseCaseService()
    maker = _actor("maker")
    with pytest.raises(CaseAccessError):
        service.create(actor=maker, scope=service.evidence.scope.model_copy(update={"period": "2026-08"}),
                       department_ids=_DEPTS, idempotency_key="foreign")
    case = service.create(actor=maker, scope=service.evidence.scope, department_ids=_DEPTS, idempotency_key="create")
    with pytest.raises(CaseStateError):
        service.supersede_evidence(case.case_id.value, actor=maker, department_ids=_DEPTS,
                                   expected_revision=case.revision, idempotency_key="bad", source_type="client_status")
