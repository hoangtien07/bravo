from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core_v2.case_state import (
    AccountingCase, CaseStateError, CorruptCaseState, IdempotencyConflict,
    InMemoryCaseRepository, RevisionConflict, ScopeViolation, payload_hash,
)
from app.core_v2.contracts import (
    AccountingCaseId, ApprovalEnvelope, CaseActor, CaseState, CaseTransition, CaseType,
    DraftAction, EvidenceSnapshot,
)
from app.core_v2.wp01_schema import ScopeKey


_NOW = datetime(2026, 7, 31, 9, tzinfo=timezone.utc)


def _scope(**changes) -> ScopeKey:
    payload = {
        "tenant_id": "tenant-a", "legal_entity_id": "entity-a", "ledger_id": "ledger-a",
        "period": "2026-07", "cutoff": "2026-07-31", "currency": "VND",
        "environment": "synthetic-demo", "bravo_version": "B10R1", "config_version": "v1",
        "bank_account_ref": "1121-001",
    }
    payload.update(changes)
    return ScopeKey.model_validate(payload)


def _case() -> AccountingCase:
    return AccountingCase(AccountingCaseId(value="case_12345678"), CaseType.BANK_RECONCILIATION, _scope())


def _transition(case: AccountingCase, to_state: CaseState, key: str) -> CaseTransition:
    return CaseTransition(
        from_state=case.state, to_state=to_state,
        actor=CaseActor(user_id="maker-a", role="preparer", scope_ref="dept-a"),
        preconditions=(), expected_revision=case.revision, idempotency_key=key,
    )


def _snapshot(snapshot_id: str, *, complete: bool = True, supersedes: str | None = None,
              scope: ScopeKey | None = None) -> EvidenceSnapshot:
    return EvidenceSnapshot(
        snapshot_id=snapshot_id, source_type="bank_statement", source_version="v1", cutoff=_NOW,
        captured_at=_NOW, content_hash="a" * 64, supersedes=supersedes, complete=complete,
        scope=scope or _scope(),
    )


def _advance_to_evidence_pending(repo: InMemoryCaseRepository, case: AccountingCase) -> AccountingCase:
    case = repo.transition(case.case_id, _transition(case, CaseState.SCOPE_LOCKED, "scope"))
    return repo.transition(case.case_id, _transition(case, CaseState.EVIDENCE_PENDING, "pending"))


def test_transition_table_requires_scope_and_complete_evidence_before_checking():
    repo = InMemoryCaseRepository()
    case = _advance_to_evidence_pending(repo, repo.create(_case()))
    with pytest.raises(CaseStateError, match="incomplete"):
        repo.transition(case.case_id, _transition(case, CaseState.EVIDENCE_READY, "ready-empty"))

    case = repo.attach_evidence(case.case_id, _snapshot("snapshot-1"), expected_revision=case.revision,
                                idempotency_key="evidence-1")
    assert case.state is CaseState.EVIDENCE_READY
    case = repo.transition(case.case_id, _transition(case, CaseState.CHECKED, "checked"))
    assert case.state is CaseState.CHECKED and case.revision == 4


def test_revision_cas_and_idempotency_are_fail_closed():
    repo = InMemoryCaseRepository()
    case = repo.create(_case())
    first = repo.transition(case.case_id, _transition(case, CaseState.SCOPE_LOCKED, "same-request"))
    assert repo.transition(case.case_id, _transition(case, CaseState.SCOPE_LOCKED, "same-request")) == first
    with pytest.raises(RevisionConflict):
        repo.transition(case.case_id, _transition(case, CaseState.SCOPE_LOCKED, "stale"))
    with pytest.raises(IdempotencyConflict):
        repo.transition(case.case_id, _transition(case, CaseState.EVIDENCE_PENDING, "same-request"))


def test_superseded_evidence_resets_case_and_invalidates_approval():
    repo = InMemoryCaseRepository()
    case = _advance_to_evidence_pending(repo, repo.create(_case()))
    case = repo.attach_evidence(case.case_id, _snapshot("snapshot-1"), expected_revision=case.revision,
                                idempotency_key="evidence-1")
    payload = {"export": "reconciliation-packet"}
    action = DraftAction(action_type="export", target_capability="packet", payload=payload,
                         source_snapshot_ids=("snapshot-1",), payload_hash=payload_hash(payload))
    case = repo.bind_draft_action(case.case_id, action, expected_revision=case.revision, idempotency_key="draft")
    approval = ApprovalEnvelope(maker_id="maker-a", checker_id="checker-b", payload_hash=action.payload_hash,
                                policy_version="v1", approved_at=_NOW)
    case = repo.approve(case.case_id, approval, expected_revision=case.revision, idempotency_key="approval")
    case = repo.attach_evidence(case.case_id, _snapshot("snapshot-2", supersedes="snapshot-1"),
                                expected_revision=case.revision, idempotency_key="supersede")
    assert case.state is CaseState.EVIDENCE_READY
    assert case.approval is None and [item.snapshot_id for item in case.evidence] == ["snapshot-2"]


def test_payload_change_invalidates_prior_approval_and_scope_cannot_widen():
    repo = InMemoryCaseRepository()
    case = _advance_to_evidence_pending(repo, repo.create(_case()))
    case = repo.attach_evidence(case.case_id, _snapshot("snapshot-1"), expected_revision=case.revision,
                                idempotency_key="evidence-1")
    first_payload = {"export": "one"}
    first = DraftAction(action_type="export", target_capability="packet", payload=first_payload,
                        source_snapshot_ids=("snapshot-1",), payload_hash=payload_hash(first_payload))
    case = repo.bind_draft_action(case.case_id, first, expected_revision=case.revision, idempotency_key="first")
    case = repo.approve(case.case_id, ApprovalEnvelope(maker_id="maker", checker_id="checker",
                        payload_hash=first.payload_hash, policy_version="v1", approved_at=_NOW),
                        expected_revision=case.revision, idempotency_key="approve")
    second_payload = {"export": "two"}
    second = DraftAction(action_type="export", target_capability="packet", payload=second_payload,
                         source_snapshot_ids=("snapshot-1",), payload_hash=payload_hash(second_payload))
    case = repo.bind_draft_action(case.case_id, second, expected_revision=case.revision, idempotency_key="second")
    assert case.approval is None
    with pytest.raises(ScopeViolation):
        repo.attach_evidence(case.case_id, _snapshot("bad", scope=_scope(tenant_id="tenant-b")),
                             expected_revision=case.revision, idempotency_key="wrong-scope")


def test_corrupt_in_memory_state_is_explicit_failure():
    repo = InMemoryCaseRepository()
    case = repo.create(_case())
    repo._cases[case.case_id.value] = object()  # simulate corrupt persisted payload
    with pytest.raises(CorruptCaseState):
        repo.get(case.case_id)


def test_core_v2_domain_imports_no_web_database_or_model_runtime():
    prohibited = ("fastapi", "sqlalchemy", "asyncpg", "psycopg", "openai", "httpx", "pydantic_ai", "vector")
    root = Path("app/core_v2")
    for path in root.glob("*.py"):
        contents = path.read_text(encoding="utf-8").lower()
        assert not any(f"import {name}" in contents or f"from {name}" in contents for name in prohibited), path
