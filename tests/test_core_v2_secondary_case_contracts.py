from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core_v2.secondary_case_contracts import PeriodPrerequisiteInput, VoucherEvidenceInput


def test_voucher_contract_requires_decimal_money_and_no_blank_document():
    item = VoucherEvidenceInput(invoice_total=Decimal("110"), invoice_tax=Decimal("10"), invoice_net=Decimal("100"))
    assert item.invoice_total == Decimal("110")
    with pytest.raises(ValidationError):
        VoucherEvidenceInput(invoice_total=Decimal("110"), invoice_tax=Decimal("10"), invoice_net=Decimal("100"), bravo_document_id="")


def test_period_contract_rejects_required_not_applicable_prerequisite():
    with pytest.raises(ValidationError):
        PeriodPrerequisiteInput(prerequisite_id="bank", required=True, status="not_applicable", evidence_fresh=False)
