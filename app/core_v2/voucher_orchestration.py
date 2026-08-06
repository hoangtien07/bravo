"""Durable bounded Voucher Evidence & Accounting Review case service."""
from __future__ import annotations

import uuid
from decimal import Decimal

from app.core_v2.bank_orchestration import SyntheticBankCaseService, _RuntimeCase
from app.core_v2.case_state import AccountingCase, CaseStateError, payload_hash
from app.core_v2.contracts import (
    AccountingCaseId, CaseActor, CaseState, CaseType,
    DeterministicCheckResult, DraftAction, Finding, FindingSeverity,
)
from app.core_v2.synthetic_voucher_adapter import SyntheticVoucherEvidenceSource
from app.core_v2.wp01_schema import ScopeKey


class SyntheticVoucherCaseService(SyntheticBankCaseService):
    """The client selects no accounting facts; all evidence comes from the frozen scenario."""

    def __init__(self, evidence: SyntheticVoucherEvidenceSource | None = None) -> None:
        super().__init__(evidence=evidence or SyntheticVoucherEvidenceSource())  # type: ignore[arg-type]
        self.evidence: SyntheticVoucherEvidenceSource

    def create(self, *, actor: CaseActor, scope: ScopeKey, department_ids: frozenset[str],
               idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        self._authorize(actor, department_ids, "create")
        if scope != self.evidence.scope:
            from app.core_v2.bank_orchestration import CaseAccessError
            raise CaseAccessError("only the frozen synthetic Voucher scope is enabled")
        fingerprint = self._hash({"scope": scope.model_dump(mode="json"), "case_type": CaseType.VOUCHER_EVIDENCE_REVIEW.value})
        cached = self._replay(actor.user_id, "create", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        case = AccountingCase(AccountingCaseId(value=f"case_{uuid.uuid4().hex}"), CaseType.VOUCHER_EVIDENCE_REVIEW,
                              scope, required_evidence_sources=self.evidence.required_sources)
        case = self.repo.create(case)
        self._runtime[case.case_id.value] = _RuntimeCase(actor.user_id, department_ids)
        case = self._transition(case, actor, CaseState.SCOPE_LOCKED, f"{idempotency_key}:scope")
        case = self._transition(case, actor, CaseState.EVIDENCE_PENDING, f"{idempotency_key}:pending")
        self._record(actor.user_id, "create", idempotency_key, fingerprint, case)
        return case

    def attach_evidence(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str],
                        expected_revision: int, idempotency_key: str) -> AccountingCase:
        self._require(idempotency_key)
        case = self.get(case_id, actor=actor, department_ids=department_ids)
        self._authorize_case(case, actor, department_ids, "write")
        fingerprint = self._hash({"expected_revision": expected_revision, "sources": sorted(self.evidence.required_sources)})
        cached = self._replay(case_id, "attach_evidence", idempotency_key, fingerprint)
        if cached is not None:
            return cached  # type: ignore[return-value]
        for kind in sorted(self.evidence.required_sources):
            snapshot = self.evidence.capture(kind, case.scope)  # type: ignore[arg-type]
            case = self.repo.attach_evidence(case.case_id, snapshot, expected_revision=expected_revision,
                                             idempotency_key=f"{idempotency_key}:{kind}")
            expected_revision = case.revision
        self._record(case_id, "attach_evidence", idempotency_key, fingerprint, case)
        return case

    def supersede_evidence(self, case_id: str, *, actor: CaseActor, department_ids: frozenset[str],
                            expected_revision: int, idempotency_key: str, source_type: str) -> AccountingCase:
        self._require(idempotency_key)
        if source_type not in self.evidence.required_sources:
            raise CaseStateError("unsupported synthetic Voucher evidence source")
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
        runtime.results, runtime.findings, runtime.review_decisions = (), (), ()
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
        checks = self._checks()
        snapshots = tuple(item.snapshot_id for item in case.evidence)
        typed = tuple(DeterministicCheckResult(check_id=f"voucher-check-{index:03d}",
                      rule_version="voucher-evidence-review/v1.0.0", inputs={"server_fixture": "voucher-evidence-review-golden/v1.0.0"},
                      result={"status": status}, reason_code=reason, lineage_snapshot_ids=snapshots)
                      for index, (_, status, reason) in enumerate(checks, 1))
        findings = tuple(Finding(finding_id=f"finding-{index:03d}", finding_type=check_id,
                    severity=FindingSeverity.HIGH if status == "fail" else FindingSeverity.MEDIUM,
                    status="open", evidence_snapshot_ids=snapshots, check_result_ids=(typed[index - 1].check_id,))
                    for index, (check_id, status, _) in enumerate(checks, 1) if status != "pass")
        case = self._transition(case, actor, CaseState.CHECKED, f"{idempotency_key}:checked", expected_revision)
        evidence_hash = self._evidence_hash(case)
        result_hash = self._hash([item.model_dump(mode="json") for item in typed])
        draft = {"artifact_type": "voucher-evidence-review-packet", "case_id": case_id,
                 "evidence_hash": evidence_hash, "result_hash": result_hash,
                 "execution": "artifact produced; BRAVO did not create, post, or change a voucher."}
        action = DraftAction(action_type="export", target_capability="voucher_evidence_review_packet", payload=draft,
                             source_snapshot_ids=snapshots, payload_hash=payload_hash(draft))
        case = self.repo.bind_draft_action(case.case_id, action, expected_revision=case.revision,
                                           idempotency_key=f"{idempotency_key}:draft")
        case = self._transition(case, actor, CaseState.NEEDS_REVIEW, f"{idempotency_key}:review", case.revision)
        runtime = self._runtime[case_id]
        runtime.results, runtime.findings = typed, findings
        self._record(case_id, "run_checks", idempotency_key, fingerprint, case)
        return case

    def _checks(self) -> tuple[tuple[str, str, str], ...]:
        invoice = self.evidence.payload("invoice")
        po = self.evidence.payload("purchase_order_or_contract")
        receipt = self.evidence.payload("receipt_or_qc")
        draft = self.evidence.payload("bravo_draft_voucher")
        duplicates = self.evidence.payload("duplicate_registry")
        tax = self.evidence.payload("tax_master_policy")
        dimension = self.evidence.payload("account_dimension_policy")
        total_ok = invoice["total"] == str(Decimal(invoice["net"]) + Decimal(invoice["tax"]))
        tax_ok = invoice["tax_rate"] in tax["allowed_tax_rates"] and Decimal(invoice["tax"]) == Decimal(invoice["net"]) * Decimal(invoice["tax_rate"])
        return (
            ("document_total", "pass" if total_ok else "fail", "TOTAL_RECONCILES" if total_ok else "TOTAL_MISMATCH"),
            ("tax_arithmetic", "pass" if tax_ok else "fail", "TAX_POLICY_MATCH" if tax_ok else "TAX_POLICY_MISMATCH"),
            ("duplicate_candidate", "fail" if invoice["invoice_number"] in duplicates["invoice_numbers"] else "pass", "DUPLICATE_DOCUMENT" if invoice["invoice_number"] in duplicates["invoice_numbers"] else "NO_DUPLICATE"),
            ("three_way_evidence", "pass" if po["approved_amount"] == invoice["total"] and receipt["accepted"] else "fail", "THREE_WAY_MATCH" if po["approved_amount"] == invoice["total"] and receipt["accepted"] else "THREE_WAY_MISMATCH"),
            ("master_reference", "pass" if invoice["supplier_id"] == po["supplier_id"] == draft["supplier_id"] else "fail", "SUPPLIER_MATCH" if invoice["supplier_id"] == po["supplier_id"] == draft["supplier_id"] else "SUPPLIER_MISMATCH"),
            ("account_dimension_eligibility", "pass" if draft["account_code"] in dimension["allowed_account_codes"] and draft["dimension_code"] in dimension["allowed_dimension_codes"] else "fail", "ACCOUNT_DIMENSION_ELIGIBLE" if draft["account_code"] in dimension["allowed_account_codes"] and draft["dimension_code"] in dimension["allowed_dimension_codes"] else "ACCOUNT_DIMENSION_INELIGIBLE"),
            ("evidence_coverage", "pass", "SERVER_RESOLVED_COMPLETE_EVIDENCE"),
        )
