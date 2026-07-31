"""Pure in-memory AccountingCase state machine and CAS contracts (WP-02)."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from typing import Callable

from app.core_v2.contracts import (
    AccountingCaseId, ApprovalEnvelope, CaseState, CaseTransition, CaseType, DraftAction,
    EvidenceSnapshot, ScopeKey,
)


class CaseStateError(ValueError):
    pass


class RevisionConflict(CaseStateError):
    pass


class IdempotencyConflict(CaseStateError):
    pass


class CorruptCaseState(CaseStateError):
    pass


class ScopeViolation(CaseStateError):
    pass


_NORMAL_TRANSITIONS: dict[CaseState, frozenset[CaseState]] = {
    CaseState.NEW: frozenset({CaseState.SCOPE_LOCKED}),
    CaseState.SCOPE_LOCKED: frozenset({CaseState.EVIDENCE_PENDING}),
    CaseState.EVIDENCE_PENDING: frozenset({CaseState.EVIDENCE_READY}),
    CaseState.EVIDENCE_READY: frozenset({CaseState.CHECKED, CaseState.EVIDENCE_PENDING}),
    CaseState.CHECKED: frozenset({CaseState.NEEDS_REVIEW, CaseState.EVIDENCE_PENDING}),
    CaseState.NEEDS_REVIEW: frozenset({CaseState.REVIEWED, CaseState.EVIDENCE_PENDING}),
    CaseState.REVIEWED: frozenset({CaseState.EXPORTED, CaseState.EVIDENCE_PENDING}),
    CaseState.EXPORTED: frozenset({CaseState.CLOSED, CaseState.EVIDENCE_PENDING}),
}
_SIDE_STATES = frozenset({CaseState.ABSTAINED, CaseState.FAILED, CaseState.CANCELLED, CaseState.SUPERSEDED})


def payload_hash(payload: dict) -> str:
    """Canonical payload hash; payload-bound approval must use this exact representation."""
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class AccountingCase:
    case_id: AccountingCaseId
    case_type: CaseType
    scope: ScopeKey
    state: CaseState = CaseState.NEW
    revision: int = 0
    evidence: tuple[EvidenceSnapshot, ...] = ()
    draft_action: DraftAction | None = None
    approval: ApprovalEnvelope | None = None

    def evidence_complete(self) -> bool:
        return bool(self.evidence) and all(item.complete for item in self.evidence)


@dataclass(frozen=True)
class _IdempotentOutcome:
    operation: str
    fingerprint: str
    result: AccountingCase


def validate_transition(case: AccountingCase, transition: CaseTransition) -> None:
    if transition.from_state != case.state:
        raise CaseStateError("transition from_state does not match case state")
    if transition.expected_revision != case.revision:
        raise RevisionConflict("expected revision is stale")
    if transition.to_state in _SIDE_STATES:
        return
    allowed = _NORMAL_TRANSITIONS.get(case.state, frozenset())
    if transition.to_state not in allowed:
        raise CaseStateError(f"invalid transition: {case.state} -> {transition.to_state}")
    if transition.to_state == CaseState.EVIDENCE_READY and not case.evidence_complete():
        raise CaseStateError("required evidence is incomplete")
    if transition.to_state == CaseState.CHECKED and not case.evidence_complete():
        raise CaseStateError("cannot check without complete evidence")


class InMemoryCaseRepository:
    """Test adapter that enforces CAS and idempotency without persistence or web dependencies."""

    def __init__(self) -> None:
        self._cases: dict[str, AccountingCase] = {}
        self._idempotency: dict[tuple[str, str], _IdempotentOutcome] = {}

    def create(self, case: AccountingCase) -> AccountingCase:
        if case.case_id.value in self._cases:
            raise CaseStateError("case ID already exists")
        self._cases[case.case_id.value] = case
        return case

    def get(self, case_id: AccountingCaseId) -> AccountingCase:
        value = self._cases.get(case_id.value)
        if not isinstance(value, AccountingCase):
            raise CorruptCaseState("persisted case is missing or corrupt")
        return value

    def transition(self, case_id: AccountingCaseId, transition: CaseTransition) -> AccountingCase:
        return self._apply(
            case_id, transition.idempotency_key, "transition",
            f"{transition.from_state}:{transition.to_state}:{transition.expected_revision}",
            transition.expected_revision,
            lambda case: self._transition(case, transition),
        )

    def attach_evidence(self, case_id: AccountingCaseId, snapshot: EvidenceSnapshot, *,
                        expected_revision: int, idempotency_key: str) -> AccountingCase:
        if not idempotency_key:
            raise CaseStateError("idempotency key is required")
        fingerprint = f"{snapshot.snapshot_id}:{snapshot.content_hash}:{expected_revision}"
        return self._apply(
            case_id, idempotency_key, "attach_evidence", fingerprint, expected_revision,
            lambda case: self._attach_evidence(case, snapshot),
        )

    def bind_draft_action(self, case_id: AccountingCaseId, action: DraftAction, *,
                          expected_revision: int, idempotency_key: str) -> AccountingCase:
        if action.payload_hash != payload_hash(action.payload):
            raise CaseStateError("draft action payload hash does not match payload")
        fingerprint = f"{action.payload_hash}:{expected_revision}"
        return self._apply(
            case_id, idempotency_key, "bind_draft_action", fingerprint, expected_revision,
            lambda case: self._bind_draft_action(case, action),
        )

    def approve(self, case_id: AccountingCaseId, approval: ApprovalEnvelope, *,
                expected_revision: int, idempotency_key: str) -> AccountingCase:
        fingerprint = f"{approval.payload_hash}:{approval.policy_version}:{expected_revision}"
        return self._apply(
            case_id, idempotency_key, "approve", fingerprint, expected_revision,
            lambda case: self._approve(case, approval),
        )

    @staticmethod
    def assert_scope(scope: ScopeKey, requested_scope: ScopeKey) -> None:
        if requested_scope != scope:
            raise ScopeViolation("requested scope differs from the locked case scope")

    def _apply(self, case_id: AccountingCaseId, idempotency_key: str, operation: str, fingerprint: str,
               expected_revision: int, mutation: Callable[[AccountingCase], AccountingCase]) -> AccountingCase:
        key = (case_id.value, idempotency_key)
        previous = self._idempotency.get(key)
        if previous:
            if previous.operation == operation and previous.fingerprint == fingerprint:
                return previous.result
            raise IdempotencyConflict("idempotency key was already used for another request")
        case = self.get(case_id)
        if case.revision != expected_revision:
            raise RevisionConflict("expected revision is stale")
        result = mutation(case)
        self._cases[case_id.value] = result
        self._idempotency[key] = _IdempotentOutcome(operation, fingerprint, result)
        return result

    @staticmethod
    def _transition(case: AccountingCase, transition: CaseTransition) -> AccountingCase:
        validate_transition(case, transition)
        return replace(case, state=transition.to_state, revision=case.revision + 1)

    @staticmethod
    def _attach_evidence(case: AccountingCase, snapshot: EvidenceSnapshot) -> AccountingCase:
        InMemoryCaseRepository.assert_scope(case.scope, snapshot.scope)
        existing = tuple(item for item in case.evidence if item.snapshot_id != snapshot.supersedes)
        if any(item.snapshot_id == snapshot.snapshot_id for item in existing):
            raise CaseStateError("evidence snapshot ID already exists")
        next_evidence = (*existing, snapshot)
        next_state = CaseState.EVIDENCE_READY if all(item.complete for item in next_evidence) else CaseState.EVIDENCE_PENDING
        return replace(case, evidence=next_evidence, state=next_state, revision=case.revision + 1,
                       approval=None)

    @staticmethod
    def _bind_draft_action(case: AccountingCase, action: DraftAction) -> AccountingCase:
        if not set(action.source_snapshot_ids).issubset({item.snapshot_id for item in case.evidence}):
            raise CaseStateError("draft action references unknown evidence")
        approval = case.approval if case.approval and case.approval.payload_hash == action.payload_hash else None
        return replace(case, draft_action=action, approval=approval, revision=case.revision + 1)

    @staticmethod
    def _approve(case: AccountingCase, approval: ApprovalEnvelope) -> AccountingCase:
        if case.draft_action is None or case.draft_action.payload_hash != approval.payload_hash:
            raise CaseStateError("approval payload hash does not match current draft")
        return replace(case, approval=approval, revision=case.revision + 1)
