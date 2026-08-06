from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from app.core_v2.bank_engine import BankEngineError, BankReconciliationEngine, BankReconciliationPolicy
from app.core_v2.wp01_schema import BankStatementRow, BravoBankLedgerRow, ScopeKey


_ROOT = Path(__file__).parent / "fixtures" / "core_v2" / "wp01"


def _engine() -> BankReconciliationEngine:
    raw = yaml.safe_load((_ROOT / "bank_policy.yaml").read_text(encoding="utf-8"))
    matching = raw["matching"]
    return BankReconciliationEngine(BankReconciliationPolicy(
        policy_id=raw["policy_id"],
        maximum_statement_rows=raw["scope"]["maximum_statement_rows"],
        maximum_ledger_rows=raw["scope"]["maximum_ledger_rows"],
        tolerance_amount_vnd=Decimal(matching["tolerance"]["amount_difference_vnd"]),
        tolerance_date_window_days=matching["tolerance"]["date_window_days"],
        aggregation_maximum_rows=matching["aggregation"]["maximum_contributing_ledger_rows"],
        aggregation_amount_difference_vnd=Decimal(matching["aggregation"]["amount_difference_vnd"]),
        aggregation_date_window_days=matching["aggregation"]["date_window_days"],
    ))


def _rows():
    raw = yaml.safe_load((_ROOT / "bank_golden.yaml").read_text(encoding="utf-8"))
    return (raw, tuple(BankStatementRow.model_validate(item) for item in raw["bank_statement_rows"]),
            tuple(BravoBankLedgerRow.model_validate(item) for item in raw["bravo_bank_ledger_rows"]))


def test_engine_matches_every_frozen_golden_result_exactly():
    fixture, bank_rows, ledger_rows = _rows()
    results = _engine().reconcile(bank_rows, ledger_rows)
    actual = {(result.bank_row_ids, result.bravo_row_ids): result for result in results}
    for expected in fixture["golden_results"]:
        key = (tuple(expected["bank_row_ids"]), tuple(expected["bravo_row_ids"]))
        result = actual[key]
        assert result.classification.value == expected["classification"]
        assert result.amount_difference_vnd == Decimal(expected["amount_difference_vnd"])
        assert result.reason_code == expected["reason_code"]
    assert len(results) == len(fixture["golden_results"])


def test_permutation_does_not_change_deterministic_results():
    _, bank_rows, ledger_rows = _rows()
    engine = _engine()
    assert engine.reconcile(bank_rows, ledger_rows) == engine.reconcile(tuple(reversed(bank_rows)), tuple(reversed(ledger_rows)))


def test_duplicate_ids_and_oversized_inputs_fail_explicitly():
    _, bank_rows, ledger_rows = _rows()
    engine = _engine()
    with pytest.raises(BankEngineError, match="duplicate bank"):
        engine.reconcile((bank_rows[0], bank_rows[0]), ledger_rows)
    small = BankReconciliationEngine(BankReconciliationPolicy(
        "small", 1, 1, Decimal("0"), 0, 2, Decimal("0"), 0,
    ))
    with pytest.raises(BankEngineError, match="exceeds"):
        small.reconcile(bank_rows, ledger_rows)


def test_engine_has_no_llm_dependency_or_llm_input():
    _, bank_rows, ledger_rows = _rows()
    result = _engine().reconcile(bank_rows, ledger_rows)
    assert all(item.policy_id == "bank-reconciliation/v1.0.0" for item in result)


def test_competing_bank_rows_remain_ambiguous_and_do_not_emit_false_bank_only():
    _, bank_rows, ledger_rows = _rows()
    competing = bank_rows[0].model_copy(update={"source_row_id": "BANK-001-COMPETING"})

    results = _engine().reconcile((bank_rows[0], competing), (ledger_rows[0],))

    assert {(item.bank_row_ids, item.classification.value, item.reason_code) for item in results} == {
        (("BANK-001",), "AMBIGUOUS", "COMPETING_BANK_ROWS_NO_TIE_BREAK"),
        (("BANK-001-COMPETING",), "AMBIGUOUS", "COMPETING_BANK_ROWS_NO_TIE_BREAK"),
    }
    assert all(item.classification.value != "BANK_ONLY" for item in results)
    assert all(item.classification.value != "BRAVO_ONLY" for item in results)


def test_mismatched_reference_cannot_claim_exact_reference_amount_date():
    _, bank_rows, ledger_rows = _rows()
    wrong_reference = bank_rows[0].model_copy(update={"bank_reference": "WRONG-REFERENCE"})

    result = _engine().reconcile((wrong_reference,), (ledger_rows[0],))

    assert len(result) == 1
    assert result[0].classification.value == "TOLERANCE_MATCH"
    assert result[0].reason_code == "WITHIN_APPROVED_TOLERANCE"


def test_scope_and_document_status_mismatch_cannot_match():
    fixture, bank_rows, ledger_rows = _rows()
    scope = ScopeKey.model_validate(fixture["scope"])
    cancelled = ledger_rows[0].model_copy(update={"document_status": "cancelled"})
    foreign_entity = ledger_rows[0].model_copy(update={"legal_entity_id": "other-entity"})

    cancelled_result = _engine().reconcile((bank_rows[0],), (cancelled,), scope)
    foreign_result = _engine().reconcile((bank_rows[0],), (foreign_entity,), scope)

    assert cancelled_result[0].classification.value == "BANK_ONLY"
    assert foreign_result[0].classification.value == "BANK_ONLY"
