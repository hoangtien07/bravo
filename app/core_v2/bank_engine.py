"""Deterministic Bank statement ↔ BRAVO bank-ledger reconciliation engine (WP-03)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from itertools import combinations

from app.core_v2.wp01_schema import BankStatementRow, BravoBankLedgerRow


class BankResultClass(StrEnum):
    EXACT_MATCH = "EXACT_MATCH"
    TOLERANCE_MATCH = "TOLERANCE_MATCH"
    AGGREGATED_CANDIDATE = "AGGREGATED_CANDIDATE"
    DUPLICATE_CANDIDATE = "DUPLICATE_CANDIDATE"
    BANK_ONLY = "BANK_ONLY"
    BRAVO_ONLY = "BRAVO_ONLY"
    AMBIGUOUS = "AMBIGUOUS"
    INVALID_INPUT = "INVALID_INPUT"


class BankEngineError(ValueError):
    pass


@dataclass(frozen=True)
class BankReconciliationPolicy:
    policy_id: str
    maximum_statement_rows: int
    maximum_ledger_rows: int
    tolerance_amount_vnd: Decimal
    tolerance_date_window_days: int
    aggregation_maximum_rows: int
    aggregation_amount_difference_vnd: Decimal
    aggregation_date_window_days: int

    def __post_init__(self) -> None:
        if not self.policy_id or self.maximum_statement_rows <= 0 or self.maximum_ledger_rows <= 0:
            raise BankEngineError("policy limits and ID must be positive/non-empty")
        if self.tolerance_amount_vnd < 0 or self.aggregation_amount_difference_vnd < 0:
            raise BankEngineError("policy amounts cannot be negative")
        if self.tolerance_date_window_days < 0 or self.aggregation_date_window_days < 0:
            raise BankEngineError("policy date windows cannot be negative")
        if self.aggregation_maximum_rows < 2:
            raise BankEngineError("aggregation requires at least two rows")


@dataclass(frozen=True)
class BankCheckResult:
    classification: BankResultClass
    bank_row_ids: tuple[str, ...]
    bravo_row_ids: tuple[str, ...]
    amount_difference_vnd: Decimal
    reason_code: str
    policy_id: str
    features: tuple[str, ...]


def _date_distance(left: date, right: date) -> int:
    return abs((left - right).days)


class BankReconciliationEngine:
    """Pure, bounded matching; ambiguous candidates are never selected by ranking or an LLM."""

    def __init__(self, policy: BankReconciliationPolicy) -> None:
        self.policy = policy

    def reconcile(self, bank_rows: tuple[BankStatementRow, ...] | list[BankStatementRow],
                  ledger_rows: tuple[BravoBankLedgerRow, ...] | list[BravoBankLedgerRow]) -> tuple[BankCheckResult, ...]:
        if len(bank_rows) > self.policy.maximum_statement_rows or len(ledger_rows) > self.policy.maximum_ledger_rows:
            raise BankEngineError("input exceeds approved policy limit")
        banks = tuple(sorted(bank_rows, key=lambda item: item.source_row_id))
        ledgers = tuple(sorted(ledger_rows, key=lambda item: item.bravo_row_id))
        self._assert_unique_ids(banks, ledgers)
        available = {item.bravo_row_id: item for item in ledgers}
        results: list[BankCheckResult] = []

        for bank in banks:
            result, consumed = self._classify_bank_row(bank, tuple(available.values()))
            results.append(result)
            for row_id in consumed:
                available.pop(row_id, None)
        for ledger in sorted(available.values(), key=lambda item: item.bravo_row_id):
            results.append(BankCheckResult(
                BankResultClass.BRAVO_ONLY, (), (ledger.bravo_row_id,), ledger.normalized_signed_amount,
                "NO_ELIGIBLE_BANK_ROW", self.policy.policy_id, ("unmatched_ledger",),
            ))
        return tuple(results)

    @staticmethod
    def _assert_unique_ids(banks: tuple[BankStatementRow, ...], ledgers: tuple[BravoBankLedgerRow, ...]) -> None:
        if len({item.source_row_id for item in banks}) != len(banks):
            raise BankEngineError("duplicate bank source row ID")
        if len({item.bravo_row_id for item in ledgers}) != len(ledgers):
            raise BankEngineError("duplicate BRAVO ledger row ID")

    def _classify_bank_row(self, bank: BankStatementRow,
                            available: tuple[BravoBankLedgerRow, ...]) -> tuple[BankCheckResult, tuple[str, ...]]:
        eligible = tuple(row for row in available if self._same_scope(bank, row))
        duplicate = tuple(row for row in eligible if bank.bank_reference and row.reference_id == bank.bank_reference
                          and row.normalized_signed_amount == bank.normalized_signed_amount)
        if len(duplicate) > 1:
            return self._result(BankResultClass.DUPLICATE_CANDIDATE, bank, duplicate,
                                "DUPLICATE_REFERENCE_AND_SIGNED_AMOUNT"), tuple(row.bravo_row_id for row in duplicate)

        exact = tuple(row for row in eligible if row.normalized_signed_amount == bank.normalized_signed_amount
                      and _date_distance(bank.transaction_date, row.posting_date) == 0)
        if len(exact) == 1:
            return self._result(BankResultClass.EXACT_MATCH, bank, exact, "EXACT_REFERENCE_AMOUNT_DATE"), (exact[0].bravo_row_id,)
        if len(exact) > 1:
            return self._result(BankResultClass.AMBIGUOUS, bank, exact,
                                "MULTIPLE_ELIGIBLE_ROWS_NO_TIE_BREAK"), tuple(row.bravo_row_id for row in exact)

        tolerance = tuple(row for row in eligible if self._within_tolerance(bank, row))
        if len(tolerance) == 1:
            return self._result(BankResultClass.TOLERANCE_MATCH, bank, tolerance,
                                "WITHIN_APPROVED_TOLERANCE"), (tolerance[0].bravo_row_id,)
        if len(tolerance) > 1:
            return self._result(BankResultClass.AMBIGUOUS, bank, tolerance,
                                "MULTIPLE_ELIGIBLE_ROWS_NO_TIE_BREAK"), tuple(row.bravo_row_id for row in tolerance)

        aggregation = self._aggregation_candidates(bank, eligible)
        if len(aggregation) == 1:
            return self._result(BankResultClass.AGGREGATED_CANDIDATE, bank, aggregation[0],
                                "TWO_LEDGER_ROWS_WITHIN_AGGREGATION_LIMIT"), tuple(row.bravo_row_id for row in aggregation[0])
        if len(aggregation) > 1:
            flattened = tuple(row for group in aggregation for row in group)
            return self._result(BankResultClass.AMBIGUOUS, bank, flattened,
                                "MULTIPLE_AGGREGATIONS_NO_TIE_BREAK"), tuple(sorted({row.bravo_row_id for row in flattened}))

        return self._result(BankResultClass.BANK_ONLY, bank, (), "NO_ELIGIBLE_BRAVO_ROW"), ()

    @staticmethod
    def _same_scope(bank: BankStatementRow, ledger: BravoBankLedgerRow) -> bool:
        return bank.account_ref == ledger.account_ref and bank.currency == ledger.currency

    def _within_tolerance(self, bank: BankStatementRow, ledger: BravoBankLedgerRow) -> bool:
        return (_date_distance(bank.transaction_date, ledger.posting_date) <= self.policy.tolerance_date_window_days
                and abs(bank.normalized_signed_amount - ledger.normalized_signed_amount) <= self.policy.tolerance_amount_vnd)

    def _aggregation_candidates(self, bank: BankStatementRow,
                                eligible: tuple[BravoBankLedgerRow, ...]) -> tuple[tuple[BravoBankLedgerRow, ...], ...]:
        candidates: list[tuple[BravoBankLedgerRow, ...]] = []
        for size in range(2, self.policy.aggregation_maximum_rows + 1):
            for group in combinations(eligible, size):
                if any(_date_distance(bank.transaction_date, row.posting_date) > self.policy.aggregation_date_window_days
                       for row in group):
                    continue
                difference = bank.normalized_signed_amount - sum((row.normalized_signed_amount for row in group), Decimal("0"))
                if abs(difference) <= self.policy.aggregation_amount_difference_vnd:
                    candidates.append(group)
        return tuple(candidates)

    def _result(self, classification: BankResultClass, bank: BankStatementRow,
                ledgers: tuple[BravoBankLedgerRow, ...], reason_code: str) -> BankCheckResult:
        ledger_total = sum((row.normalized_signed_amount for row in ledgers), Decimal("0"))
        difference = bank.normalized_signed_amount - ledger_total
        if classification is BankResultClass.TOLERANCE_MATCH:
            difference = abs(difference)
        elif classification in {BankResultClass.DUPLICATE_CANDIDATE, BankResultClass.AMBIGUOUS}:
            difference = min((abs(bank.normalized_signed_amount - row.normalized_signed_amount)
                              for row in ledgers), default=Decimal("0"))
        return BankCheckResult(
            classification, (bank.source_row_id,), tuple(row.bravo_row_id for row in ledgers),
            difference, reason_code, self.policy.policy_id,
            ("same_account", "same_currency"),
        )
