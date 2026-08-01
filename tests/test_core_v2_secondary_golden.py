from decimal import Decimal
from pathlib import Path

import yaml

from app.core_v2.period_close_engine import ClosePrerequisite, ReconciliationReference, assess_period_close
from app.core_v2.voucher_engine import VoucherEvidence, review_voucher


ROOT = Path(__file__).parent / "fixtures" / "core_v2" / "dev_secondary"


def test_voucher_developer_golden_cases_match_deterministic_engine_and_are_not_sme_truth():
    fixture = yaml.safe_load((ROOT / "voucher_golden.yaml").read_text(encoding="utf-8"))
    assert fixture["truth_status"] == "developer_synthetic_only_not_sme_approved"
    for case in fixture["cases"]:
        raw = case["evidence"]
        evidence = VoucherEvidence(invoice_total=Decimal(raw["invoice_total"]), invoice_tax=Decimal(raw["invoice_tax"]),
                                   invoice_net=Decimal(raw["invoice_net"]), po_amount=Decimal(raw["po_amount"]) if raw["po_amount"] else None,
                                   received=raw["received"], bravo_document_id=raw["bravo_document_id"],
                                   duplicate_document_ids=tuple(raw["duplicate_document_ids"]))
        got = {item.check_id: item.status for item in review_voucher(evidence)}
        assert {key: got[key] for key in case["expected"]} == case["expected"]


def test_period_close_developer_golden_cases_fail_closed_and_are_not_sme_truth():
    fixture = yaml.safe_load((ROOT / "period_close_golden.yaml").read_text(encoding="utf-8"))
    assert fixture["truth_status"] == "developer_synthetic_only_not_sme_approved"
    for case in fixture["cases"]:
        result = assess_period_close(tuple(ClosePrerequisite(**item) for item in case["prerequisites"]),
                                     tuple(ReconciliationReference(**item) for item in case["reconciliations"]))
        assert result.ready is case["expected_ready"]
        if not result.ready:
            assert case["expected_reason"] in result.reason_codes
