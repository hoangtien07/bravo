from app.core_v2.bank_orchestration import CaseAccessError
from app.core_v2.case_state import CaseStateError
from app.core_v2.contracts import CaseActor, CaseState, ReviewDecision
from app.core_v2.voucher_orchestration import SyntheticVoucherCaseService
import pytest


_DEPTS = frozenset({"dept-a"})


def _actor(user_id: str, role: str = "preparer") -> CaseActor:
    return CaseActor(user_id=user_id, role=role, scope_ref="dept-a")


def _decisions(service: SyntheticVoucherCaseService, view: dict, reviewer: CaseActor) -> tuple[ReviewDecision, ...]:
    out = []
    for finding in view["findings"]:
        draft = ReviewDecision(finding_id=finding["finding_id"], disposition="investigate",
                               reviewer_id=reviewer.user_id, reason_code="REVIEW_PENDING",
                               decision_hash="0" * 64)
        out.append(draft.model_copy(update={"decision_hash": service.review_decision_hash(draft)}))
    return tuple(out)


def test_voucher_case_uses_server_fixture_and_completes_durable_lifecycle():
    service = SyntheticVoucherCaseService()
    maker = _actor("maker")
    case = service.create(actor=maker, scope=service.evidence.scope, department_ids=_DEPTS, idempotency_key="create")
    case = service.attach_evidence(case.case_id.value, actor=maker, department_ids=_DEPTS,
                                   expected_revision=case.revision, idempotency_key="evidence")
    assert case.state is CaseState.EVIDENCE_READY
    case = service.run_checks(case.case_id.value, actor=maker, department_ids=_DEPTS,
                              expected_revision=case.revision, idempotency_key="checks")
    view = service.view(case)
    assert {item["result"]["status"] for item in view["results"]} == {"pass"}
    assert case.draft_action is not None
    assert "BRAVO did not create, post, or change a voucher" in case.draft_action.payload["execution"]

    reviewer = _actor("checker", "reviewer")
    case = service.review(case.case_id.value, actor=reviewer, department_ids=_DEPTS,
                          expected_revision=case.revision, idempotency_key="review",
                          decisions=_decisions(service, view, reviewer),
                          payload_hash_value=view["draft_payload_hash"], evidence_hash=view["evidence_hash"],
                          result_hash=view["result_hash"])
    reviewed = service.view(case)
    case, artifact = service.export(case.case_id.value, actor=reviewer, department_ids=_DEPTS,
                                    expected_revision=case.revision, idempotency_key="export",
                                    payload_hash_value=reviewed["draft_payload_hash"], evidence_hash=reviewed["evidence_hash"],
                                    review_hash=reviewed["approval"]["review_hash"])
    assert case.state is CaseState.EXPORTED
    assert artifact["status"] == "artifact_produced_not_executed"


def test_voucher_client_cannot_substitute_scope_or_evidence_source():
    service = SyntheticVoucherCaseService()
    maker = _actor("maker")
    with pytest.raises(CaseAccessError):
        service.create(actor=maker, scope=service.evidence.scope.model_copy(update={"tenant_id": "other"}),
                       department_ids=_DEPTS, idempotency_key="foreign")
    case = service.create(actor=maker, scope=service.evidence.scope, department_ids=_DEPTS, idempotency_key="create")
    with pytest.raises(CaseStateError):
        service.supersede_evidence(case.case_id.value, actor=maker, department_ids=_DEPTS,
                                   expected_revision=case.revision, idempotency_key="bad", source_type="fabricated")
