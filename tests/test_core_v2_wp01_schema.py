from decimal import Decimal
import hashlib
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


def test_golden_pack_covers_every_locked_bank_result_class_once_or_more():
    fixture = _load("bank_golden.yaml")
    classes = {result["classification"] for result in fixture["golden_results"]}
    assert classes == {
        "EXACT_MATCH", "TOLERANCE_MATCH", "AGGREGATED_CANDIDATE", "DUPLICATE_CANDIDATE",
        "BANK_ONLY", "BRAVO_ONLY", "AMBIGUOUS",
    }
    assert all(str(result["amount_difference_vnd"]) == result["amount_difference_vnd"]
               for result in fixture["golden_results"])


def test_pack_is_declared_synthetic_and_contains_no_credential_fields():
    for path in (*_ROOT.glob("*.json"), *_ROOT.glob("*.yaml"), _ROOT / "must_not_claims.md", _ROOT / "glossary.md"):
        contents = path.read_text(encoding="utf-8").lower()
        assert "synthetic" in contents
        assert "api_key" not in contents
        assert "password" not in contents


def test_fixture_manifest_hashes_every_declared_artifact():
    manifest = json.loads((_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "bravo-accounting-case-wp01-manifest/v1"
    assert manifest["review_status"] == "pending_independent_sme_review"
    assert {item["path"] for item in manifest["artifacts"]} == {
        "bank_golden.yaml", "held_out_manifest.json", "bank_policy.yaml", "voucher_schema.yaml",
        "period_close_schema.yaml", "must_not_claims.md", "glossary.md",
    }
    for artifact in manifest["artifacts"]:
        digest = hashlib.sha256((_ROOT / artifact["path"]).read_bytes()).hexdigest()
        assert artifact["sha256"] == digest


def test_held_out_truth_is_not_shipped_to_the_implementation_worktree():
    held_out = json.loads((_ROOT / "held_out_manifest.json").read_text(encoding="utf-8"))
    assert held_out["repository_payload"] is False
    assert held_out["case_count"] == 4
    assert "expected_classification" not in json.dumps(held_out)
    assert not (_ROOT / "bank_held_out.yaml").exists()


def test_checksum_file_also_covers_the_manifest():
    lines = (_ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    checksums = dict(line.split("  ", 1) for line in lines if line)
    for name, expected in checksums.items():
        assert hashlib.sha256((_ROOT / expected).read_bytes()).hexdigest() == name
    assert "manifest.json" in checksums.values()
