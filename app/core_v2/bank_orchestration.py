"""Imperative WP-04 orchestration for the durable synthetic Bank case.

The service keeps only privacy-minimised result and trace references while enforcing the Core V2
CAS/idempotency contracts. SQL persistence is supplied by the outer adapter.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import uuid

from app.core_v2.bank_engine import BankResultClass
from app.core_v2.case_state import AccountingCase, CaseStateError, InMemoryCaseRepository, payload_hash
from app.core_v2.contracts import (
    AccountingCaseId, CaseActor, CaseState, CaseTransition, CaseType, DeterministicCheckResult,
    ApprovalEnvelope, DraftAction, Finding, FindingSeverity,
    ReviewDecision,
)
from app.core_v2.synthetic_bank_adapter import SyntheticBankEvidenceSource
from app.core_v2.wp01_schema import ScopeKey


class CaseAccessError(PermissionError):
    pass


@dataclass
class _RuntimeCase:
    owner_id: str
    department_ids: frozenset[str]
    results: tuple[DeterministicCheckResult, ...] = ()
    findings: tuple[Finding, ...] = ()
    review_decisions: tuple[ReviewDecision, ...] = ()
    exports: dict[str, dict] = field(default_factory=dict)


@dataclass(frozen=True)
class _CommandOutcome:
    operation: str
    request_hash: str
    outcome: object


def _severity(kind: BankResultClass) -> FindingSeverity:
    if kind in {BankResultClass.BANK_ONLY, BankResultClass.BRAVO_ONLY}:
        return FindingSeverity.HIGH
    if kind in {BankResultClass.DUPLICATE_CANDIDATE, BankResultClass.AMBIGUOUS}:
        return FindingSeverity.MEDIUM
    return FindingSeverity.INFO


class SyntheticBankCaseService:
    """Application adapter: no LLM, BRAVO API, raw evidence audit payload, or live IDs."""

    def __init__(self, evidence: SyntheticBankEvidenceSource | None = None) -> None:
        self.evidence = evidence or SyntheticBankEvidenceSource()
        self.repo = InMemoryCaseRepository()
        self._runtime: dict[str, _RuntimeCase] = {}
        self._commands: dict[tuple[str, str], _CommandOutcome] = {}

    def create(self, *, actor: CaseActor, scope: ScopeKey, department_ids: frozenset[str],
               idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        self._authorize(actor, department_ids, "create")
        if scope != self.evidence.scope:
            raise CaseAccessError("only the frozen synthetic Bank scope is enabled")
        fingerprint = self._hash({"scope": scope.model_dump(mode="json")})
        cached = self._replay(actor.user_id, "create", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        case = AccountingCase(AccountingCaseId(value=f"case_{uuid.uuid4().hex}"), CaseType.BANK_RECONCILIATION, scope,
                              required_evidence_sources=frozenset({"bank_statement", "bravo_bank_ledger"}))
        case = self.repo.create(case)
        self._runtime[case.case_id.value] = _RuntimeCase(actor.user_id, department_ids)
        case = self._transition(case, actor, CaseState.SCOPE_LOCKED, f"{idempotency_key}:scope")
        case = self._transition(case, actor, CaseState.EVIDENCE_PENDING, f"{idempotency_key}:pending")
        self._record(actor.user_id, "create", idempotency_key, fingerprint, case)
        return case

    def get(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str]) -> AccountingCase:
        case = self.repo.get(AccountingCaseId(value=case_id))
        self._authorize_case(case, actor, department_ids, "read")
        return case

    def list_accessible(self, *, actor: CaseActor, department_ids: frozenset[str]) -> list[AccountingCase]:
        cases: list[AccountingCase] = []
        for case_id in self._runtime:
            try:
                cases.append(self.get(case_id, actor=actor, department_ids=department_ids))
            except CaseAccessError:
                continue
        return cases

    def attach_evidence(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str],
                        expected_revision: int, idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "write")
        fingerprint = self._hash({"expected_revision": expected_revision, "sources": ["bank_statement", "bravo_bank_ledger"]})
        cached = self._replay(case_id, "attach_evidence", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        for kind in ("bank_statement", "bravo_bank_ledger"):
            snapshot = self.evidence.capture(kind, case.scope)  # type: ignore[arg-type]
            case = self.repo.attach_evidence(case.case_id, snapshot, expected_revision=expected_revision,
                                             idempotency_key=f"{idempotency_key}:{kind}")
            expected_revision = case.revision
        self._record(case_id, "attach_evidence", idempotency_key, fingerprint, case)
        return case

    def supersede_evidence(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str],
                            expected_revision: int, idempotency_key: str, source_type: str) -> AccountingCase:
        self._require(idempotency_key)
        if source_type not in {"bank_statement", "bravo_bank_ledger"}:
            raise CaseStateError("unsupported synthetic evidence source")
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "write")
        fingerprint = self._hash({"expected_revision": expected_revision, "source_type": source_type,
                                  "replacement": "reissued-v1"})
        cached = self._replay(case_id, "supersede_evidence", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        snapshot = self.evidence.capture(source_type, case.scope, reissued=True)  # type: ignore[arg-type]
        case = self.repo.attach_evidence(case.case_id, snapshot, expected_revision=expected_revision,
                                         idempotency_key=f"{idempotency_key}:replacement")
        runtime = self._runtime[case_id]
        runtime.results = ()
        runtime.findings = ()
        runtime.review_decisions = ()
        self._record(case_id, "supersede_evidence", idempotency_key, fingerprint, case)
        return case

    def run_checks(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str],
                   expected_revision: int, idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "write")
        fingerprint = self._hash({"expected_revision": expected_revision})
        cached = self._replay(case_id, "run_checks", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        if case.state is not CaseState.EVIDENCE_READY:
            raise CaseStateError("case must have complete current evidence before checks")
        results = self.evidence.engine().reconcile(self.evidence.bank_rows(), self.evidence.ledger_rows(), case.scope)
        snapshots = tuple(item.snapshot_id for item in case.evidence)
        typed = tuple(DeterministicCheckResult(
            check_id=f"bank-check-{index:03d}", rule_version=result.policy_id,
            inputs={"bank_row_ids": result.bank_row_ids, "bravo_row_ids": result.bravo_row_ids},
            result={"classification": result.classification.value, "amount_difference_vnd": str(result.amount_difference_vnd)},
            reason_code=result.reason_code, lineage_snapshot_ids=snapshots,
        ) for index, result in enumerate(results, 1))
        findings = tuple(Finding(
            finding_id=f"finding-{index:03d}", finding_type=result.classification.value,
            severity=_severity(result.classification), status="open", evidence_snapshot_ids=snapshots,
            check_result_ids=(typed[index - 1].check_id,),
        ) for index, result in enumerate(results, 1) if result.classification not in {BankResultClass.EXACT_MATCH, BankResultClass.TOLERANCE_MATCH})
        case = self._transition(case, actor, CaseState.CHECKED, f"{idempotency_key}:checked", expected_revision)
        evidence_hash = self._evidence_hash(case)
        result_hash = self._hash([item.model_dump(mode="json") for item in typed])
        draft_payload = {"artifact_type": "bank-reconciliation-packet", "case_id": case_id,
                         "evidence_hash": evidence_hash, "result_hash": result_hash,
                         "result_ids": [item.check_id for item in typed],
                         "execution": "artifact produced; BRAVO did not execute anything."}
        action = DraftAction(action_type="export", target_capability="bank_reconciliation_packet",
                             payload=draft_payload, source_snapshot_ids=tuple(item.snapshot_id for item in case.evidence),
                             payload_hash=payload_hash(draft_payload))
        case = self.repo.bind_draft_action(case.case_id, action, expected_revision=case.revision,
                                           idempotency_key=f"{idempotency_key}:draft")
        case = self._transition(case, actor, CaseState.NEEDS_REVIEW, f"{idempotency_key}:review", case.revision)
        runtime = self._runtime[case_id]
        runtime.results, runtime.findings = typed, findings
        self._record(case_id, "run_checks", idempotency_key, fingerprint, case)
        return case

    def review(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str], expected_revision: int,
               idempotency_key: str, decisions: tuple[ReviewDecision, ...], payload_hash_value: str,
               evidence_hash: str, result_hash: str) -> AccountingCase:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        runtime = self._runtime[case_id]
        self._authorize_case(case, actor, department_ids, "review")
        fingerprint = self._hash({"expected_revision": expected_revision, "decisions": [item.model_dump(mode="json") for item in decisions],
                                  "payload_hash": payload_hash_value, "evidence_hash": evidence_hash,
                                  "result_hash": result_hash})
        cached = self._replay(case_id, "review", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        if actor.user_id == runtime.owner_id:
            raise CaseAccessError("maker cannot review their own Bank case")
        finding_ids = {item.finding_id for item in runtime.findings}
        if {item.finding_id for item in decisions} != finding_ids or len(decisions) != len(finding_ids):
            raise CaseStateError("every current finding requires one reviewer disposition")
        for decision in decisions:
            if decision.reviewer_id != actor.user_id:
                raise CaseAccessError("review decision reviewer does not match the acting reviewer")
            if decision.decision_hash != self.review_decision_hash(decision):
                raise CaseStateError("review decision hash does not match its immutable contents")
        if case.draft_action is None or case.draft_action.payload_hash != payload_hash_value:
            raise CaseStateError("review payload hash does not match the current draft")
        if evidence_hash != self._evidence_hash(case):
            raise CaseStateError("review evidence hash does not match current evidence")
        if result_hash != self._hash([item.model_dump(mode="json") for item in runtime.results]):
            raise CaseStateError("review result hash does not match current checks")
        review_hash = self._hash({"decisions": [item.model_dump(mode="json") for item in decisions],
                                  "reviewer": actor.user_id, "revision": case.revision})
        approval = ApprovalEnvelope(maker_id=runtime.owner_id, checker_id=actor.user_id,
                                    payload_hash=case.draft_action.payload_hash, policy_version="bank-review/v1",
                                    approved_at=datetime.now(timezone.utc), evidence_hash=evidence_hash,
                                    result_hash=result_hash, review_hash=review_hash)
        case = self.repo.approve(case.case_id, approval, expected_revision=expected_revision,
                                 idempotency_key=f"{idempotency_key}:approval")
        case = self._transition(case, actor, CaseState.REVIEWED, f"{idempotency_key}:review", case.revision)
        runtime.review_decisions = decisions
        self._record(case_id, "review", idempotency_key, fingerprint, case)
        return case

    def export(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str], expected_revision: int,
               idempotency_key: str, payload_hash_value: str, evidence_hash: str,
               review_hash: str) -> tuple[AccountingCase, dict]:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "export")
        fingerprint = self._hash({"expected_revision": expected_revision, "payload_hash": payload_hash_value,
                                  "evidence_hash": evidence_hash, "review_hash": review_hash})
        cached = self._replay(case_id, "export", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        runtime = self._runtime[case_id]
        if case.state is not CaseState.REVIEWED:
            raise CaseStateError("a reviewed case is required before export")
        if case.draft_action is None or case.approval is None:
            raise CaseStateError("reviewed and approved export draft is required")
        approval = case.approval
        if (payload_hash_value != case.draft_action.payload_hash or approval.payload_hash != payload_hash_value
                or evidence_hash != approval.evidence_hash or review_hash != approval.review_hash):
            raise CaseStateError("export envelope does not match approved draft/evidence/review")
        payload = {**case.draft_action.payload, "review_decisions": [item.model_dump(mode="json") for item in runtime.review_decisions],
                   "review_hash": approval.review_hash, "checker_id": approval.checker_id}
        case = self._transition(case, actor, CaseState.EXPORTED, f"{idempotency_key}:export", expected_revision)
        artifact = {"payload_hash": case.draft_action.payload_hash, "status": "artifact_produced_not_executed", **payload}
        runtime.exports[case.draft_action.payload_hash] = artifact
        result = (case, artifact)
        self._record(case_id, "export", idempotency_key, fingerprint, result)
        return result

    def view(self, case: AccountingCase) -> dict:
        runtime = self._runtime[case.case_id.value]
        return {"case_id": case.case_id.value, "case_type": case.case_type.value, "scope": case.scope.model_dump(mode="json"),
                "state": case.state.value, "revision": case.revision,
                "evidence": [item.model_dump(mode="json") for item in case.evidence],
                "results": [item.model_dump(mode="json") for item in runtime.results],
                "findings": [item.model_dump(mode="json") for item in runtime.findings],
                "review_decisions": [item.model_dump(mode="json") for item in runtime.review_decisions],
                "draft_payload_hash": case.draft_action.payload_hash if case.draft_action else None,
                "evidence_hash": self._evidence_hash(case),
                "result_hash": self._hash([item.model_dump(mode="json") for item in runtime.results]) if runtime.results else None,
                "approval": case.approval.model_dump(mode="json") if case.approval else None,
                "trace": {"contract_version": "wp04/v1", "source_snapshot_ids": [item.snapshot_id for item in case.evidence],
                          "result_ids": [item.check_id for item in runtime.results], "raw_evidence_retained": False}}

    def _transition(self, case: AccountingCase, actor: CaseActor, target: CaseState, key: str, expected: int | None = None) -> AccountingCase:
        return self.repo.transition(case.case_id, CaseTransition(from_state=case.state, to_state=target, actor=actor,
            preconditions=(), expected_revision=case.revision if expected is None else expected, idempotency_key=key))

    @staticmethod
    def _require(key: str) -> None:
        if not key:
            raise CaseStateError("idempotency key is required")

    def _authorize_case(self, case: AccountingCase, actor: CaseActor, departments: frozenset[str], action: str) -> None:
        runtime = self._runtime[case.case_id.value]
        if not (departments & runtime.department_ids) and actor.role not in {"admin", "preparer_all", "reviewer_all"}:
            raise CaseAccessError("case is outside the caller's authorized department scope")
        self._authorize(actor, departments, action)

    @staticmethod
    def _authorize(actor: CaseActor, departments: frozenset[str], action: str) -> None:
        if actor.role not in {"preparer", "reviewer", "preparer_all", "reviewer_all", "admin"}:
            raise CaseAccessError("unrecognized accounting-case role")
        if not departments and actor.role != "admin":
            raise CaseAccessError("department scope is required")
        if action == "review" and actor.role not in {"reviewer", "reviewer_all", "admin"}:
            raise CaseAccessError("reviewer role is required")
        if action == "export" and actor.role not in {"reviewer", "reviewer_all", "admin"}:
            raise CaseAccessError("reviewer role is required for export")

    def _replay(self, subject: str, operation: str, key: str, request_hash: str) -> object | None:
        previous = self._commands.get((subject, key))
        if previous is None:
            return None
        if previous.operation == operation and previous.request_hash == request_hash:
            return previous.outcome
        from app.core_v2.case_state import IdempotencyConflict
        raise IdempotencyConflict("idempotency key was already used for another command or request")

    def _record(self, subject: str, operation: str, key: str, request_hash: str, outcome: object) -> None:
        self._commands[(subject, key)] = _CommandOutcome(operation, request_hash, outcome)

    @staticmethod
    def _hash(value: object) -> str:
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                         separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

    @classmethod
    def review_decision_hash(cls, decision: ReviewDecision) -> str:
        return cls._hash({
            "finding_id": decision.finding_id,
            "disposition": decision.disposition.value,
            "reviewer_id": decision.reviewer_id,
            "reason_code": decision.reason_code,
            "note": decision.note,
            "evidence_snapshot_ids": decision.evidence_snapshot_ids,
        })

    def _evidence_hash(self, case: AccountingCase) -> str:
        return self._hash({item.snapshot_id: item.content_hash for item in case.evidence})
