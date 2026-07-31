# WP-01 case-specific must-not claims

Status: `pending_independent_sme_review`; all examples are synthetic. These claims are hard
constraints for the later deterministic engines and LLM output guards.

## Bank reconciliation

- Do not say a row reconciled unless the deterministic result and its source lineage exist.
- Do not calculate authoritative amounts, choose tolerance/materiality, waive exceptions, post an
  adjustment, pay, lock a period, or execute SQL.
- Do not match across a different bank account, currency, legal entity, ledger, or frozen scope.

## Voucher Evidence Review

- Do not claim tax or legal eligibility without an approved effective-dated policy and reviewer.
- Do not post, mutate, or create a BRAVO voucher or parallel ledger.
- Do not present a proposed account/dimension as approved or executed.

## Period Close Readiness

- Do not calculate depreciation, allocation, costing, FX, closing entries, or reports.
- Do not lock or reopen a period, or claim BRAVO executed a close.
- Do not report ready while a required dependency, fresh evidence, reconciliation blocker, or
  maker-checker approval is missing.
