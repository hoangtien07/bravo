"""Read-only adapters from V2 contracts to bounded secondary deterministic engines."""
from __future__ import annotations

from app.core_v2.period_close_engine import ClosePrerequisite, ReconciliationReference, assess_period_close
from app.core_v2.secondary_case_contracts import (
    DeterministicCheckView,
    PeriodCloseReadinessView,
    PeriodPrerequisiteInput,
    ReconciliationReferenceInput,
    VoucherEvidenceInput,
)
from app.core_v2.voucher_engine import VoucherEvidence, review_voucher


def preview_voucher_review(payload: VoucherEvidenceInput) -> tuple[DeterministicCheckView, ...]:
    checks = review_voucher(VoucherEvidence(**payload.model_dump()))
    return tuple(DeterministicCheckView(check_id=item.check_id, status=item.status, reason_code=item.reason_code) for item in checks)


def preview_period_close(prerequisites: tuple[PeriodPrerequisiteInput, ...],
                         reconciliations: tuple[ReconciliationReferenceInput, ...]) -> PeriodCloseReadinessView:
    result = assess_period_close(
        tuple(ClosePrerequisite(**item.model_dump()) for item in prerequisites),
        tuple(ReconciliationReference(**item.model_dump()) for item in reconciliations),
    )
    return PeriodCloseReadinessView(**result.__dict__)
