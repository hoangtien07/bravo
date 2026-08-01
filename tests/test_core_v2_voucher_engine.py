from decimal import Decimal

from app.core_v2.voucher_engine import VoucherEvidence, review_voucher


def test_voucher_review_detects_total_duplicate_and_three_way_failures_without_posting():
    checks = review_voucher(VoucherEvidence(Decimal("110"), Decimal("10"), Decimal("99"), Decimal("110"), True, "draft-1", ("draft-old",)))
    assert {(item.check_id, item.status) for item in checks} >= {("document_total", "fail"), ("duplicate_candidate", "fail")}
    assert all("post" not in item.reason_code.lower() for item in checks)


def test_voucher_review_abstains_for_missing_required_three_way_evidence():
    checks = review_voucher(VoucherEvidence(Decimal("110"), Decimal("10"), Decimal("100"), None, None, None))
    assert {(item.check_id, item.status) for item in checks} >= {("three_way_evidence", "abstain"), ("lineage", "abstain")}
