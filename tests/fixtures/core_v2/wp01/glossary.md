# BRAVO Accounting Intelligence — WP-01 glossary

Status: `pending_independent_sme_review`; this glossary is synthetic-fixture contract text, not
an assertion about a live BRAVO configuration.

| Term | Frozen meaning for WP-01 |
|---|---|
| `ScopeKey` | Immutable tenant, legal entity, ledger, period, cutoff, currency, environment, BRAVO version, config version, and (for Bank) account boundary. |
| Evidence snapshot | Versioned capture of a declared source at a cutoff; it is not permanent truth and may be superseded. |
| Bank credit / debit | Bank-statement signs normalized as credit = positive and debit = negative bank-balance movement. |
| BRAVO debit / credit | Ledger signs normalized as debit = positive and credit = negative bank-balance movement. |
| `EXACT_MATCH` | One eligible bank row and one eligible BRAVO row with equal normalized amount, same account and same date. |
| `TOLERANCE_MATCH` | Eligible one-to-one pair satisfying the approved date/amount tolerance but not the exact rule. |
| `AGGREGATED_CANDIDATE` | One bank row and no more than the approved number of eligible BRAVO rows satisfy the aggregation constraints; reviewer confirmation remains required. |
| `DUPLICATE_CANDIDATE` | Multiple eligible rows share the approved duplicate signals. It must never silently become an exact match. |
| `BANK_ONLY` / `BRAVO_ONLY` | A source row has no eligible counterpart after the ordered policy rules. |
| `AMBIGUOUS` | More than one eligible resolution remains and the frozen policy has no deterministic tie-break. |
| `INVALID_INPUT` | A row fails its frozen schema and is quarantined with a reason, never coerced into checking. |
| Result difference | `BANK_ONLY` and `BRAVO_ONLY` retain signed movement; tolerance uses absolute pair difference; duplicate/ambiguous use the minimum candidate difference rather than summing mutually exclusive candidates. |
| Critical false negative | A held-out critical case whose expected classification or must-not constraint is violated. |
