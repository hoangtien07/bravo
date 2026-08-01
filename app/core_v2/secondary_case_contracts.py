"""Typed synthetic input/output contracts for bounded Voucher and Period Close cases."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.core_v2.contracts import ContractModel


class VoucherEvidenceInput(ContractModel):
    invoice_total: Decimal = Field(gt=0)
    invoice_tax: Decimal = Field(ge=0)
    invoice_net: Decimal = Field(ge=0)
    po_amount: Decimal | None = Field(default=None, gt=0)
    received: bool | None = None
    bravo_document_id: str | None = None
    duplicate_document_ids: tuple[str, ...] = ()

    @field_validator("bravo_document_id")
    @classmethod
    def no_blank_document(cls, value: str | None) -> str | None:
        if value == "":
            raise ValueError("bravo_document_id cannot be blank")
        return value


class DeterministicCheckView(ContractModel):
    check_id: str
    status: Literal["pass", "fail", "abstain"]
    reason_code: str


class PeriodPrerequisiteInput(ContractModel):
    prerequisite_id: str = Field(min_length=1)
    required: bool
    status: Literal["complete", "pending", "not_applicable"]
    evidence_fresh: bool

    @model_validator(mode="after")
    def not_applicable_is_explicit(self) -> "PeriodPrerequisiteInput":
        if self.status == "not_applicable" and self.required:
            raise ValueError("a required prerequisite cannot be not_applicable")
        return self


class ReconciliationReferenceInput(ContractModel):
    case_id: str = Field(pattern=r"^case_[A-Za-z0-9_-]{8,128}$")
    status: Literal["reviewed", "unresolved", "missing"]
    material: bool


class PeriodCloseReadinessView(ContractModel):
    ready: bool
    blocker_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    execution: str
