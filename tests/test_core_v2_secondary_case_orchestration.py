from decimal import Decimal

from app.core_v2.secondary_case_contracts import (
    PeriodPrerequisiteInput,
    ReconciliationReferenceInput,
    VoucherEvidenceInput,
)
from app.core_v2.secondary_case_orchestration import preview_period_close, preview_voucher_review


def test_preview_voucher_maps_typed_contract_to_deterministic_view():
    result = preview_voucher_review(VoucherEvidenceInput(invoice_total=Decimal("110"), invoice_tax=Decimal("10"), invoice_net=Decimal("100")))
    assert {(item.check_id, item.status) for item in result} >= {("document_total", "pass"), ("three_way_evidence", "abstain")}


def test_preview_period_close_maps_typed_contract_to_fail_closed_view():
    result = preview_period_close((PeriodPrerequisiteInput(prerequisite_id="bank", required=True, status="pending", evidence_fresh=True),),
                                  (ReconciliationReferenceInput(case_id="case_12345678", status="reviewed", material=True),))
    assert result.ready is False
    assert result.reason_codes == ("REQUIRED_PREREQUISITE_INCOMPLETE",)
