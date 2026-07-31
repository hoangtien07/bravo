"""WP-01 frozen synthetic evidence schemas.

These contracts validate source material before a future deterministic engine sees it.  They
are deliberately not a reconciliation engine and do not express match policy decisions.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import re
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


SCHEMA_VERSION = "bravo-accounting-case-wp01/v1"
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _required(value: str) -> str:
    if not value:
        raise ValueError("must not be blank")
    return value


def _iso_date(value: Any) -> date:
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        raise ValueError("must be an ISO date (YYYY-MM-DD)")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("must be a valid ISO date") from exc


def _positive_decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError("must be a decimal string or Decimal, never float")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("must be a valid decimal") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError("must be a finite positive decimal")
    return parsed


class BankDirection(StrEnum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class ScopeKey(StrictModel):
    """The WP-01 scope lock; a case may not silently widen any of these fields."""

    tenant_id: str
    legal_entity_id: str
    ledger_id: str
    period: str
    cutoff: date
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    environment: str
    bravo_version: str
    config_version: str
    bank_account_ref: str | None = None

    _nonblank = field_validator(
        "tenant_id", "legal_entity_id", "ledger_id", "period", "environment",
        "bravo_version", "config_version", "bank_account_ref",
    )(_required)
    _cutoff = field_validator("cutoff", mode="before")(_iso_date)


class SourceLineage(StrictModel):
    snapshot_id: str
    source_file: str
    line_ref: str

    _nonblank = field_validator("snapshot_id", "source_file", "line_ref")(_required)


class BankStatementRow(StrictModel):
    source_row_id: str
    account_ref: str
    transaction_date: date
    value_date: date
    amount: Decimal
    direction: BankDirection
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    bank_reference: str | None = None
    description: str | None = None
    counterparty: str | None = None
    lineage: SourceLineage

    _nonblank = field_validator("source_row_id", "account_ref")(_required)
    _transaction_date = field_validator("transaction_date", mode="before")(_iso_date)
    _value_date = field_validator("value_date", mode="before")(_iso_date)
    _amount = field_validator("amount", mode="before")(_positive_decimal)

    @property
    def normalized_signed_amount(self) -> Decimal:
        """Bank credit increases the bank balance; debit decreases it."""
        return self.amount if self.direction is BankDirection.CREDIT else -self.amount


class BravoBankLedgerRow(StrictModel):
    bravo_row_id: str
    legal_entity_id: str
    account_ref: str
    ledger_id: str
    posting_date: date
    document_date: date
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    document_id: str
    voucher_id: str
    reference_id: str | None = None
    description: str | None = None
    counterparty: str | None = None
    lineage: SourceLineage

    _nonblank = field_validator(
        "bravo_row_id", "legal_entity_id", "account_ref", "ledger_id", "document_id", "voucher_id",
    )(_required)
    _posting_date = field_validator("posting_date", mode="before")(_iso_date)
    _document_date = field_validator("document_date", mode="before")(_iso_date)
    _debit = field_validator("debit", mode="before")(_positive_decimal)
    _credit = field_validator("credit", mode="before")(_positive_decimal)

    @model_validator(mode="after")
    def exactly_one_side(self) -> "BravoBankLedgerRow":
        # Zero is permitted before this check, but only one non-zero side may remain.
        if (self.debit == 0) == (self.credit == 0):
            raise ValueError("exactly one of debit or credit must be positive")
        return self

    @property
    def normalized_signed_amount(self) -> Decimal:
        """Debit increases the bank asset balance; credit decreases it."""
        return self.debit - self.credit


T = TypeVar("T", bound=BaseModel)


class QuarantinedRow(StrictModel):
    source_row_id: str | None = None
    reason_code: str
    errors: tuple[str, ...]


class ValidationBatch(Generic[T]):
    def __init__(self, valid: list[T], quarantined: list[QuarantinedRow]) -> None:
        self.valid = tuple(valid)
        self.quarantined = tuple(quarantined)


def validate_rows(model: type[T], raw_rows: list[dict[str, Any]]) -> ValidationBatch[T]:
    """Validate rows without coercion; malformed source rows are quarantined explicitly."""
    valid: list[T] = []
    quarantined: list[QuarantinedRow] = []
    for raw in raw_rows:
        try:
            valid.append(model.model_validate(raw))
        except ValidationError as exc:
            row_id = raw.get("source_row_id") or raw.get("bravo_row_id")
            quarantined.append(QuarantinedRow(
                source_row_id=str(row_id) if row_id is not None else None,
                reason_code="INVALID_REQUIRED_FIELD",
                errors=tuple(error["msg"] for error in exc.errors()),
            ))
    return ValidationBatch(valid, quarantined)
