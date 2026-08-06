"""Deterministic Bank statement ↔ BRAVO bank-ledger reconciliation engine (WP-03)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from itertools import combinations

from app.core_v2.wp01_schema import BankStatementRow, BravoBankLedgerRow
from app.core_v2.wp01_schema import ScopeKey


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
    eligible_document_statuses: frozenset[str] = frozenset({"completed", "locked"})

    def __post_init__(self) -> None:
        if not self.policy_id or self.maximum_statement_rows <= 0 or self.maximum_ledger_rows <= 0:
            raise BankEngineError("policy limits and ID must be positive/non-empty")
        if self.tolerance_amount_vnd < 0 or self.aggregation_amount_difference_vnd < 0:
            raise BankEngineError("policy amounts cannot be negative")
        if self.tolerance_date_window_days < 0 or self.aggregation_date_window_days < 0:
            raise BankEngineError("policy date windows cannot be negative")
        if self.aggregation_maximum_rows < 2:
            raise BankEngineError("aggregation requires at least two rows")
        if not self.eligible_document_statuses:
            raise BankEngineError("at least one eligible document status is required")


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
                  ledger_rows: tuple[BravoBankLedgerRow, ...] | list[BravoBankLedgerRow],
                  scope: ScopeKey | None = None) -> tuple[BankCheckResult, ...]:
        if len(bank_rows) > self.policy.maximum_statement_rows or len(ledger_rows) > self.policy.maximum_ledger_rows:
            raise BankEngineError("input exceeds approved policy limit")
        banks = tuple(sorted(bank_rows, key=lambda item: item.source_row_id))
        ledgers = tuple(sorted(ledger_rows, key=lambda item: item.bravo_row_id))
        self._assert_unique_ids(banks, ledgers)
        # Classify against the complete compatibility graph first.  A greedy pass used
        # to let the first Bank row consume a BRAVO row that was also a valid candidate
        # for a later row; the later row then appeared as BANK_ONLY.  Candidate rows are
        # evidence for review, never settlement authority.
        results = [self._classify_bank_row(bank, ledgers, scope) for bank in banks]
        results = self._mark_competing_single_row_matches(results)
        candidate_ledger_ids = {
            ledger_id
            for result in results
            for ledger_id in result.bravo_row_ids
        }
        for ledger in ledgers:
            if ledger.bravo_row_id in candidate_ledger_ids:
                continue
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
                            ledger_rows: tuple[BravoBankLedgerRow, ...], scope: ScopeKey | None) -> BankCheckResult:
        eligible = tuple(row for row in ledger_rows if self._same_scope(bank, row, scope))
        duplicate = tuple(row for row in eligible if bank.bank_reference and row.reference_id == bank.bank_reference
                          and row.normalized_signed_amount == bank.normalized_signed_amount)
        if len(duplicate) > 1:
            return self._result(BankResultClass.DUPLICATE_CANDIDATE, bank, duplicate,
                                "DUPLICATE_REFERENCE_AND_SIGNED_AMOUNT")

        exact = tuple(row for row in eligible if row.normalized_signed_amount == bank.normalized_signed_amount
                      and _date_distance(bank.transaction_date, row.posting_date) == 0
                      and bank.bank_reference is not None
                      and row.reference_id is not None
                      and row.reference_id == bank.bank_reference)
        if len(exact) == 1:
            return self._result(BankResultClass.EXACT_MATCH, bank, exact, "EXACT_REFERENCE_AMOUNT_DATE")
        if len(exact) > 1:
            return self._result(BankResultClass.AMBIGUOUS, bank, exact,
                                "MULTIPLE_ELIGIBLE_ROWS_NO_TIE_BREAK")

        tolerance = tuple(row for row in eligible if self._within_tolerance(bank, row))
        if len(tolerance) == 1:
            return self._result(BankResultClass.TOLERANCE_MATCH, bank, tolerance,
                                "WITHIN_APPROVED_TOLERANCE")
        if len(tolerance) > 1:
            return self._result(BankResultClass.AMBIGUOUS, bank, tolerance,
                                "MULTIPLE_ELIGIBLE_ROWS_NO_TIE_BREAK")

        aggregation = self._aggregation_candidates(bank, eligible)
        if len(aggregation) == 1:
            return self._result(BankResultClass.AGGREGATED_CANDIDATE, bank, aggregation[0],
                                "TWO_LEDGER_ROWS_WITHIN_AGGREGATION_LIMIT")
        if len(aggregation) > 1:
            flattened = tuple(row for group in aggregation for row in group)
            return self._result(BankResultClass.AMBIGUOUS, bank, flattened,
                                "MULTIPLE_AGGREGATIONS_NO_TIE_BREAK")

        return self._result(BankResultClass.BANK_ONLY, bank, (), "NO_ELIGIBLE_BRAVO_ROW")

    def _mark_competing_single_row_matches(
            self, results: list[BankCheckResult]) -> list[BankCheckResult]:
        """Downgrade a would-be match when its ledger row is shared by any Bank candidate."""
        banks_by_ledger: dict[str, set[str]] = {}
        for result in results:
            bank_id = result.bank_row_ids[0]
            for ledger_id in result.bravo_row_ids:
                banks_by_ledger.setdefault(ledger_id, set()).add(bank_id)

        adjusted: list[BankCheckResult] = []
        for result in results:
            is_single_match = result.classification in {
                BankResultClass.EXACT_MATCH, BankResultClass.TOLERANCE_MATCH,
            } and len(result.bravo_row_ids) == 1
            if is_single_match and len(banks_by_ledger[result.bravo_row_ids[0]]) > 1:
                adjusted.append(BankCheckResult(
                    BankResultClass.AMBIGUOUS, result.bank_row_ids, result.bravo_row_ids,
                    result.amount_difference_vnd, "COMPETING_BANK_ROWS_NO_TIE_BREAK",
                    result.policy_id, result.features + ("competing_bank_candidate",),
                ))
            else:
                adjusted.append(result)
        return adjusted

    def _same_scope(self, bank: BankStatementRow, ledger: BravoBankLedgerRow, scope: ScopeKey | None) -> bool:
        if bank.account_ref != ledger.account_ref or bank.currency != ledger.currency:
            return False
        if ledger.document_status not in self.policy.eligible_document_statuses:
            return False
        if scope is None:
            return True
        return (
            bank.transaction_date <= scope.cutoff
            and ledger.posting_date <= scope.cutoff
            and ledger.legal_entity_id == scope.legal_entity_id
            and ledger.ledger_id == scope.ledger_id
            and ledger.currency == scope.currency
            and (scope.bank_account_ref is None or ledger.account_ref == scope.bank_account_ref)
        )

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
