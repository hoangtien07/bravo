"""Durable bounded Period Close Readiness case service."""
from __future__ import annotations

import uuid

from app.core_v2.bank_orchestration import SyntheticBankCaseService, _RuntimeCase
from app.core_v2.case_state import AccountingCase, CaseStateError, payload_hash
from app.core_v2.contracts import (
    AccountingCaseId, CaseActor, CaseState, CaseType, DeterministicCheckResult,
    DraftAction, Finding, FindingSeverity,
)
from app.core_v2.synthetic_period_close_adapter import SyntheticPeriodCloseEvidenceSource
from app.core_v2.wp01_schema import ScopeKey


class SyntheticPeriodCloseCaseService(SyntheticBankCaseService):
    def __init__(self, evidence: SyntheticPeriodCloseEvidenceSource | None = None) -> None:
        super().__init__(evidence=evidence or SyntheticPeriodCloseEvidenceSource())  # type: ignore[arg-type]
        self.evidence: SyntheticPeriodCloseEvidenceSource

    def create(self, *, actor: CaseActor, scope: ScopeKey, department_ids: frozenset[str], idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        self._authorize(actor, department_ids, "create")
        if scope != self.evidence.scope:
            from app.core_v2.bank_orchestration import CaseAccessError
            raise CaseAccessError("only the frozen synthetic Period Close scope is enabled")
        fingerprint = self._hash({"scope": scope.model_dump(mode="json"), "case_type": CaseType.PERIOD_CLOSE_READINESS.value})
        cached = self._replay(actor.user_id, "create", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        case = AccountingCase(AccountingCaseId(value=f"case_{uuid.uuid4().hex}"), CaseType.PERIOD_CLOSE_READINESS,
                              scope, required_evidence_sources=self.evidence.required_sources)
        case = self.repo.create(case)
        self._runtime[case.case_id.value] = _RuntimeCase(actor.user_id, department_ids)
        case = self._transition(case, actor, CaseState.SCOPE_LOCKED, f"{idempotency_key}:scope")
        case = self._transition(case, actor, CaseState.EVIDENCE_PENDING, f"{idempotency_key}:pending")
        self._record(actor.user_id, "create", idempotency_key, fingerprint, case)
        return case

    def attach_evidence(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str], expected_revision: int, idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "write")
        fingerprint = self._hash({"expected_revision": expected_revision, "sources": sorted(self.evidence.required_sources)})
        cached = self._replay(case_id, "attach_evidence", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        for kind in sorted(self.evidence.required_sources):
            case = self.repo.attach_evidence(case.case_id, self.evidence.capture(kind, case.scope),
                                             expected_revision=expected_revision, idempotency_key=f"{idempotency_key}:{kind}")
            expected_revision = case.revision
        self._record(case_id, "attach_evidence", idempotency_key, fingerprint, case)
        return case

    def supersede_evidence(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str], expected_revision: int, idempotency_key: str, source_type: str) -> AccountingCase:
        self._require(idempotency_key)
        if source_type not in self.evidence.required_sources:
            raise CaseStateError("unsupported synthetic Period Close evidence source")
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "write")
        fingerprint = self._hash({"expected_revision": expected_revision, "source_type": source_type, "replacement": "reissued-v1"})
        cached = self._replay(case_id, "supersede_evidence", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        case = self.repo.attach_evidence(case.case_id, self.evidence.capture(source_type, case.scope, reissued=True),
                                         expected_revision=expected_revision, idempotency_key=f"{idempotency_key}:replacement")
        runtime = self._runtime[case_id]
        runtime.results, runtime.findings, runtime.review_decisions = (), (), ()
        self._record(case_id, "supersede_evidence", idempotency_key, fingerprint, case)
        return case

    def run_checks(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str], expected_revision: int, idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "write")
        fingerprint = self._hash({"expected_revision": expected_revision})
        cached = self._replay(case_id, "run_checks", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        if case.state is not CaseState.EVIDENCE_READY:
            raise CaseStateError("case must have complete current evidence before checks")
        checks = self._checks()
        snapshots = tuple(item.snapshot_id for item in case.evidence)
        typed = tuple(DeterministicCheckResult(check_id=f"period-close-check-{n:03d}", rule_version="period-close-readiness/v1.0.0",
                      inputs={"server_fixture": "period-close-readiness-golden/v1.0.0"}, result={"status": state},
                      reason_code=reason, lineage_snapshot_ids=snapshots) for n, (_, state, reason) in enumerate(checks, 1))
        findings = tuple(Finding(finding_id=f"finding-{n:03d}", finding_type=kind,
                    severity=FindingSeverity.HIGH, status="open", evidence_snapshot_ids=snapshots,
                    check_result_ids=(typed[n - 1].check_id,)) for n, (kind, state, _) in enumerate(checks, 1) if state != "pass")
        case = self._transition(case, actor, CaseState.CHECKED, f"{idempotency_key}:checked", expected_revision)
        evidence_hash, result_hash = self._evidence_hash(case), self._hash([item.model_dump(mode="json") for item in typed])
        draft = {"artifact_type": "period-close-readiness-handoff", "case_id": case_id, "evidence_hash": evidence_hash,
                 "result_hash": result_hash, "ready": not findings,
                 "execution": "artifact produced; BRAVO did not execute close, calculations, reports, or period lock."}
        action = DraftAction(action_type="export", target_capability="period_close_readiness_handoff", payload=draft,
                             source_snapshot_ids=snapshots, payload_hash=payload_hash(draft))
        case = self.repo.bind_draft_action(case.case_id, action, expected_revision=case.revision, idempotency_key=f"{idempotency_key}:draft")
        case = self._transition(case, actor, CaseState.NEEDS_REVIEW, f"{idempotency_key}:review", case.revision)
        runtime = self._runtime[case_id]
        runtime.results, runtime.findings = typed, findings
        self._record(case_id, "run_checks", idempotency_key, fingerprint, case)
        return case

    def _checks(self) -> tuple[tuple[str, str, str], ...]:
        policy, statuses = self.evidence.payload("prerequisite_policy"), self.evidence.payload("process_status")
        reconciliation, approval = self.evidence.payload("reconciliation_reference"), self.evidence.payload("approval_record")
        missing = [item for item in policy["required_processes"] if statuses["statuses"].get(item) != "complete"]
        approvals_ok = all(item in approval["approvals"] and approval["approvals"][item]["maker_id"] != approval["approvals"][item]["checker_id"] for item in policy["required_approvals"])
        recon_ok = reconciliation["status"] == "reviewed" or not reconciliation["material"]
        return (
            ("required_coverage", "pass" if not missing else "fail", "REQUIRED_POLICY_COVERAGE_COMPLETE" if not missing else "REQUIRED_PREREQUISITE_INCOMPLETE"),
            ("unresolved_reconciliation", "pass" if recon_ok else "fail", "MATERIAL_RECONCILIATION_REVIEWED" if recon_ok else "MATERIAL_RECONCILIATION_UNRESOLVED"),
            ("maker_checker", "pass" if approvals_ok else "fail", "MAKER_CHECKER_COMPLETE" if approvals_ok else "MAKER_CHECKER_MISSING_OR_INVALID"),
            ("evidence_freshness", "pass", "SERVER_RESOLVED_FRESH_EVIDENCE"),
        )
