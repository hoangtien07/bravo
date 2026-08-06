# BRAVO 10 Business-flow traceability matrix

Status: `DEVELOPER-FROZEN — PENDING INDEPENDENT SME REVIEW`

Purpose: BF-00 authority map for the synthetic three-case demonstrator. This maps every
case input/check to a named BRAVO guide source or an explicit versioned synthetic policy.
It is not a claim about a customer configuration, deployment, or runtime data.

## Authority rules

1. The B10 guides are product guidance only; the manifest carries the source version, owner,
   status, effective-date availability, and customer scope.
2. An exact versioned claim must use `ExactClaimRequirement`: matching `doc_version`, an
   `approved` source, and matching/global scope. A claim requiring an as-of date also needs a
   non-null source effective date. Otherwise the retrieval result is empty/abstained.
3. The frozen YAML fixtures below are explicit synthetic policy decisions. They do not assert
   that BRAVO performed posting, payment, closing, locking, or an equivalent ERP action.

## Shared scope and lifecycle

| Contract field/control | Authority | Deterministic enforcement |
|---|---|---|
| tenant, legal entity, ledger/book, account, currency, period/cutoff | `app/core_v2/wp01_schema.py`; each `*_golden.yaml` `scope` | `ScopeKey` validation; server fixture scope equality; store scope filter/RLS |
| evidence identity, version, hash, cutoff/capture, completeness, supersession | `app/core_v2/contracts.py` `EvidenceSnapshot` | server adapters calculate SHA-256; lifecycle invalidates results/review after replacement |
| lifecycle, CAS revision and idempotency | `app/core_v2/case_state.py`, `app/adapters/accounting_case_store.py` | transactional command record; stale revision and cross-operation key fail closed |
| reviewer decision, maker/checker, hash-bound export | `app/core_v2/contracts.py` `ReviewDecision`/`ApprovalEnvelope` | typed decision hash; maker cannot review; export binds payload/evidence/result/review hashes |
| authorization and audit | `alembic/versions/0020_accounting_case_v2_audit_backstops.py` | case, command and audit RLS plus append-only audit trigger |

## Bank Reconciliation

| Evidence/check | Named business authority | Synthetic policy/implementation |
|---|---|---|
| bank statement and BRAVO money-ledger rows; dates, amounts, reference, account and currency | [Accounting guide](../../file_system/UserGuide_B10_TV_PDF/NB_UserGuide_B10_Chapter17_Accounting.pdf), [Documents guide](../../file_system/UserGuide_B10_TV_PDF/NB_UserGuide_B10_Chapter04_Documents.pdf) | `tests/fixtures/core_v2/wp01/bank_golden.yaml`; `SyntheticBankEvidenceSource` |
| legal entity, ledger, account, currency, cutoff and eligible document status | same guides; BRAVO status semantics are version/config dependent | `BravoBankLedgerRow.document_status`; `BankReconciliationEngine.reconcile(scope=...)` |
| exact reference/amount/date, tolerance, ambiguity, duplicate and aggregation classification | explicit synthetic `bank-reconciliation/v1.0.0` policy | global candidate graph in `app/core_v2/bank_engine.py`; no unresolved candidate consumption |
| extract coverage and control totals | explicit synthetic fixture policy | engine findings/rule IDs; failed coverage cannot yield reconciled conclusion |
| reviewer disposition and read-only explanation | ADR-0033 bounded case boundary | `bank_orchestration.py`; `bank_reasoning.py` cannot change deterministic findings |

## Voucher Evidence & Accounting Review

| Evidence/check | Named business authority | Synthetic policy/implementation |
|---|---|---|
| invoice identity, supplier/tax identity, UOM, quantity, net/discount/tax/gross | [Purchases guide](../../file_system/UserGuide_B10_TV_PDF/NB_UserGuide_B10_Chapter08_Purchases.pdf), [Documents guide](../../file_system/UserGuide_B10_TV_PDF/NB_UserGuide_B10_Chapter04_Documents.pdf) | `voucher_golden.yaml`: `invoice`; immutable server capture |
| PO/contract price, quantity and supplier; receipt/QC acceptance | Purchases guide | `voucher_golden.yaml`: `purchase_order_or_contract`, `receipt_or_qc` |
| BRAVO draft-voucher document, account/dimension candidate and lineage | [Accounting guide](../../file_system/UserGuide_B10_TV_PDF/NB_UserGuide_B10_Chapter17_Accounting.pdf), Documents guide | `voucher_golden.yaml`: `bravo_draft_voucher`; no caller BRAVO ID accepted |
| total and tax arithmetic; tax eligibility | Purchases/Accounting guides plus explicit effective-dated synthetic policy | `tax_master_policy`; `document_total` and `tax_arithmetic` checks |
| duplicate registry | explicit synthetic authoritative registry policy | `duplicate_registry`; `duplicate_candidate` check |
| PO/receipt/invoice match; supplier/master; account/dimension eligibility; evidence coverage | Purchases, Accounting and [Managements guide](../../file_system/UserGuide_B10_TV_PDF/NB_UserGuide_B10_Chapter05_Managements.pdf) | `three_way_evidence`, `master_reference`, `account_dimension_eligibility`, `evidence_coverage` checks |

## Period Close Readiness

| Evidence/check | Named business authority | Synthetic policy/implementation |
|---|---|---|
| required/applicable process list and dependency coverage | Accounting guide; explicit synthetic close prerequisite policy | `period_close_golden.yaml`: `prerequisite_policy`, `process_status`; client cannot supply the list |
| reconciliation state and materiality | Accounting guide; explicit synthetic policy | `reconciliation_reference`; `unresolved_reconciliation` check |
| maker/checker prerequisites | [System guide](../../file_system/UserGuide_B10_TV_PDF/NB_UserGuide_B10_Chapter06_System.pdf), Accounting guide | `approval_record`; `maker_checker` check |
| freshness, cutoff, entity/period/version and supersession | explicit synthetic evidence policy | `EvidenceSnapshot` plus `evidence_freshness` and case lifecycle invalidation |
| readiness result | Accounting guide as general workflow guidance only | `ready=true` only when every server-policy check passes; V2 does not execute close, reports, or lock |

## Must-not claims

- A passing case never means BRAVO posted a voucher, transferred funds, closed a period, or
  changed a ledger.
- Synthetic source/policy evidence is pending independent SME review and is not customer data.
- Model quality, production authorization, external model selection, and non-owner operator
  cutover are outside this BF-00 matrix.
