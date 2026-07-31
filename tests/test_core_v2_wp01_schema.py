from decimal import Decimal
import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from app.core_v2.wp01_schema import (
    BankStatementRow,
    BravoBankLedgerRow,
    ScopeKey,
    validate_rows,
)


_ROOT = Path(__file__).parent / "fixtures" / "core_v2" / "wp01"


def _load(name: str):
    return yaml.safe_load((_ROOT / name).read_text(encoding="utf-8"))


def test_bank_rows_use_decimal_iso_date_and_explicit_sign_normalization():
    fixture = _load("bank_golden.yaml")
    rows = [BankStatementRow.model_validate(row) for row in fixture["bank_statement_rows"]]
    assert rows[0].amount == Decimal("1000000")
    assert rows[0].normalized_signed_amount == Decimal("1000000")
    assert rows[1].normalized_signed_amount == Decimal("-500000")
    assert not isinstance(rows[0].amount, float)


def test_ledger_rows_require_one_posting_side_and_normalize_against_bank_balance():
    fixture = _load("bank_golden.yaml")
    rows = [BravoBankLedgerRow.model_validate(row) for row in fixture["bravo_bank_ledger_rows"]]
    assert rows[0].normalized_signed_amount == Decimal("1000000")
    assert rows[1].normalized_signed_amount == Decimal("-499900")
    with pytest.raises(ValidationError, match="exactly one"):
        BravoBankLedgerRow.model_validate({**fixture["bravo_bank_ledger_rows"][0], "credit": "1"})


@pytest.mark.parametrize("field,value", [("transaction_date", "31/07/2026"), ("amount", 1.5)])
def test_bank_rows_reject_ambiguous_dates_and_float_money(field, value):
    raw = _load("bank_golden.yaml")["bank_statement_rows"][0]
    raw[field] = value
    with pytest.raises(ValidationError):
        BankStatementRow.model_validate(raw)


def test_invalid_rows_are_quarantined_with_a_reason_not_silently_coerced():
    fixture = _load("bank_golden.yaml")
    result = validate_rows(BankStatementRow, fixture["invalid_bank_statement_rows"])
    assert not result.valid
    assert result.quarantined[0].source_row_id == "BANK-INVALID-001"
    assert result.quarantined[0].reason_code == "INVALID_REQUIRED_FIELD"


def test_scope_is_single_tenant_vnd_and_rejects_unknown_fields():
    scope = ScopeKey.model_validate(_load("bank_golden.yaml")["scope"])
    assert scope.currency == "VND"
    with pytest.raises(ValidationError):
        ScopeKey.model_validate({**scope.model_dump(mode="json"), "tenant_ids": ["other"]})


def test_fixture_manifest_hashes_every_declared_artifact():
    manifest = json.loads((_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "bravo-accounting-case-wp01-manifest/v1"
    assert manifest["review_status"] == "pending_independent_sme_review"
    assert {item["path"] for item in manifest["artifacts"]} == {
        "bank_golden.yaml", "bank_held_out.yaml", "bank_policy.yaml", "voucher_schema.yaml",
        "period_close_schema.yaml", "must_not_claims.md",
    }
