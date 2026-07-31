"""Imperative WP-04 orchestration for the synthetic Bank case.

The durable implementation is intentionally deferred: this adapter keeps the frozen demo
headless while enforcing the Core V2 CAS/idempotency contracts and retaining only minimized
result/trace references.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import uuid

from app.core_v2.bank_engine import BankResultClass
from app.core_v2.case_state import AccountingCase, CaseStateError, InMemoryCaseRepository, payload_hash
from app.core_v2.contracts import (
    AccountingCaseId, CaseActor, CaseState, CaseTransition, CaseType, DeterministicCheckResult,
    DraftAction, Finding, FindingSeverity,
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
    review_dispositions: dict[str, str] = field(default_factory=dict)
    exports: dict[str, dict] = field(default_factory=dict)


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
        self._requests: dict[tuple[str, str], object] = {}

    def create(self, *, actor: CaseActor, scope: ScopeKey, department_ids: frozenset[str],
               idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        self._authorize(actor, department_ids, "create")
        if scope != self.evidence.scope:
            raise CaseAccessError("only the frozen synthetic Bank scope is enabled")
        cached = self._cached(actor.user_id, idempotency_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        case = AccountingCase(AccountingCaseId(value=f"case_{uuid.uuid4().hex}"), CaseType.BANK_RECONCILIATION, scope)
        case = self.repo.create(case)
        self._runtime[case.case_id.value] = _RuntimeCase(actor.user_id, department_ids)
        case = self._transition(case, actor, CaseState.SCOPE_LOCKED, f"{idempotency_key}:scope")
        case = self._transition(case, actor, CaseState.EVIDENCE_PENDING, f"{idempotency_key}:pending")
        self._remember(actor.user_id, idempotency_key, case)
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
        cached = self._cached(case_id, idempotency_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        for kind in ("bank_statement", "bravo_bank_ledger"):
            snapshot = self.evidence.capture(kind, case.scope)  # type: ignore[arg-type]
            case = self.repo.attach_evidence(case.case_id, snapshot, expected_revision=expected_revision,
                                             idempotency_key=f"{idempotency_key}:{kind}")
            expected_revision = case.revision
        self._remember(case_id, idempotency_key, case)
        return case

    def run_checks(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str],
                   expected_revision: int, idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "write")
        cached = self._cached(case_id, idempotency_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        if case.state is not CaseState.EVIDENCE_READY:
            raise CaseStateError("case must have complete current evidence before checks")
        results = self.evidence.engine().reconcile(self.evidence.bank_rows(), self.evidence.ledger_rows())
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
        runtime = self._runtime[case_id]
        runtime.results, runtime.findings = typed, findings
        case = self._transition(case, actor, CaseState.CHECKED, f"{idempotency_key}:checked", expected_revision)
        case = self._transition(case, actor, CaseState.NEEDS_REVIEW, f"{idempotency_key}:review", case.revision)
        self._remember(case_id, idempotency_key, case)
        return case

    def review(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str], expected_revision: int,
               idempotency_key: str, dispositions: dict[str, str]) -> AccountingCase:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        runtime = self._runtime[case_id]
        self._authorize_case(case, actor, department_ids, "review")
        if actor.user_id == runtime.owner_id:
            raise CaseAccessError("maker cannot review their own Bank case")
        if set(dispositions) != {item.finding_id for item in runtime.findings}:
            raise CaseStateError("every current finding requires one reviewer disposition")
        runtime.review_dispositions = dict(dispositions)
        return self._transition(case, actor, CaseState.REVIEWED, idempotency_key, expected_revision)

    def export(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str], expected_revision: int,
               idempotency_key: str) -> tuple[AccountingCase, dict]:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "export")
        cached = self._cached(case_id, idempotency_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        runtime = self._runtime[case_id]
        if case.state is not CaseState.REVIEWED:
            raise CaseStateError("a reviewed case is required before export")
        payload = {"artifact_type": "bank-reconciliation-packet", "case_id": case_id,
                   "evidence_hashes": {item.snapshot_id: item.content_hash for item in case.evidence},
                   "result_ids": [item.check_id for item in runtime.results], "review": runtime.review_dispositions,
                   "execution": "artifact produced; BRAVO did not execute anything."}
        action = DraftAction(action_type="export", target_capability="bank_reconciliation_packet", payload=payload,
                             source_snapshot_ids=tuple(item.snapshot_id for item in case.evidence), payload_hash=payload_hash(payload))
        case = self.repo.bind_draft_action(case.case_id, action, expected_revision=expected_revision,
                                           idempotency_key=f"{idempotency_key}:bind")
        case = self._transition(case, actor, CaseState.EXPORTED, f"{idempotency_key}:export", case.revision)
        artifact = {"payload_hash": action.payload_hash, "status": "artifact_produced_not_executed", **payload}
        runtime.exports[action.payload_hash] = artifact
        result = (case, artifact)
        self._remember(case_id, idempotency_key, result)
        return result

    def view(self, case: AccountingCase) -> dict:
        runtime = self._runtime[case.case_id.value]
        return {"case_id": case.case_id.value, "case_type": case.case_type.value, "scope": case.scope.model_dump(mode="json"),
                "state": case.state.value, "revision": case.revision,
                "evidence": [item.model_dump(mode="json") for item in case.evidence],
                "results": [item.model_dump(mode="json") for item in runtime.results],
                "findings": [item.model_dump(mode="json") for item in runtime.findings],
                "review_dispositions": runtime.review_dispositions,
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
        if actor.user_id != runtime.owner_id and not (departments & runtime.department_ids) and actor.role != "admin":
            raise CaseAccessError("case is outside the caller's authorized department scope")
        self._authorize(actor, departments, action)

    @staticmethod
    def _authorize(actor: CaseActor, departments: frozenset[str], action: str) -> None:
        if actor.role not in {"preparer", "reviewer", "admin"}:
            raise CaseAccessError("unrecognized accounting-case role")
        if not departments and actor.role != "admin":
            raise CaseAccessError("department scope is required")
        if action == "review" and actor.role not in {"reviewer", "admin"}:
            raise CaseAccessError("reviewer role is required")
        if action == "export" and actor.role not in {"reviewer", "admin"}:
            raise CaseAccessError("reviewer role is required for export")

    def _cached(self, subject: str, key: str) -> object | None:
        return self._requests.get((subject, key))

    def _remember(self, subject: str, key: str, value: object) -> None:
        self._requests[(subject, key)] = value
