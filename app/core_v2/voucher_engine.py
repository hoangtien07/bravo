"""Bounded synthetic Voucher Evidence Review checks; never posts or creates ledger entries."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class VoucherEvidence:
    invoice_total: Decimal
    invoice_tax: Decimal
    invoice_net: Decimal
    po_amount: Decimal | None
    received: bool | None
    bravo_document_id: str | None
    duplicate_document_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class VoucherCheck:
    check_id: str
    status: str  # pass | fail | abstain
    reason_code: str


def review_voucher(evidence: VoucherEvidence) -> tuple[VoucherCheck, ...]:
    """Deterministic total/tax/duplicate/three-way coverage checks for synthetic evidence."""
    checks = [VoucherCheck("document_total", "pass" if evidence.invoice_total == evidence.invoice_net + evidence.invoice_tax else "fail",
                           "TOTAL_RECONCILES" if evidence.invoice_total == evidence.invoice_net + evidence.invoice_tax else "TOTAL_MISMATCH")]
    checks.append(VoucherCheck("duplicate_candidate", "fail" if evidence.duplicate_document_ids else "pass",
                               "DUPLICATE_DOCUMENT" if evidence.duplicate_document_ids else "NO_DUPLICATE"))
    if evidence.po_amount is None or evidence.received is None:
        checks.append(VoucherCheck("three_way_evidence", "abstain", "MISSING_PO_OR_RECEIPT"))
    elif evidence.po_amount != evidence.invoice_total or not evidence.received:
        checks.append(VoucherCheck("three_way_evidence", "fail", "THREE_WAY_MISMATCH"))
    else:
        checks.append(VoucherCheck("three_way_evidence", "pass", "THREE_WAY_MATCH"))
    checks.append(VoucherCheck("lineage", "pass" if evidence.bravo_document_id else "abstain",
                               "BRAVO_DRAFT_LINKED" if evidence.bravo_document_id else "MISSING_BRAVO_DRAFT"))
    return tuple(checks)
