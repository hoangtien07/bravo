# WP-04 Bank orchestration status

Status: `SQL/HTTP/NATIVE-RLS REMEDIATION VERIFIED IN ISOLATED POSTGRES`

Baseline at start: clean `9998d5a9a4b1f0c3b020fcd0bddbb39e5cf8ab69` on
`codex/v2-financial-close-core`. The documented pre-handoff Core V2 baseline was `3342168`;
`9998d5a` adds the WP-04 handoff documentation only. No secret store was read or copied.

## Superseded initial implementation claim

The initial process-local implementation at commit `7edcbde` was reviewed on 2026-08-01.  Its
command cache was not operation-bound, its review did not approve an exact payload, and it did
not use durable case/audit state. It must not be cited as a passed WP-04 gate. The decision and
alternatives are recorded in `evidence/v2/WP-04-REMEDIATION-DECISION.md`.

## Remediated implementation

- `SyntheticBankEvidenceSource` accepts only the frozen WP-01 bank fixture pack and its exact
  `ScopeKey`; it does not accept arbitrary paths, live BRAVO resource IDs, or a BRAVO API.
- Headless orchestration composes scope lock, two evidence snapshots, WP-03 deterministic checks,
  derived findings, reviewer dispositions, and a payload/evidence-hash-bound export artifact.
- Provisional authorized routes are under `/api/v2/accounting-cases` and are feature-flagged OFF
  by default. They use scoped `accounting_case:*:own_dept|all` permissions; creator metadata is
  not a post-revocation access bypass.
- Each mutation uses a durable SQL command ledger keyed by subject/idempotency key and bound to
  operation plus canonical request hash. Equal retries return the stored outcome; mismatches fail
  before state changes.
- Checks create a maker draft hash. An independent checker records an approval envelope bound to
  payload, evidence, result, and review-decision hashes. Export requires that exact envelope and
  states `artifact produced; BRAVO did not execute anything.`
- Case state, privacy-minimized results/findings, approval, command outcome and audit references
  are persisted by migration `0018_accounting_case_v2_shell`; raw evidence rows are not stored.

## Verification

Run on 2026-07-31 with `.venv\\Scripts\\python.exe`:

```text
pytest -q -p no:cacheprovider tests/test_core_v2_case_state.py \
  tests/test_core_v2_bank_engine.py tests/test_core_v2_bank_orchestration.py
15 passed, 1 skipped

ruff check app/core_v2/synthetic_bank_adapter.py app/core_v2/bank_orchestration.py \
  app/api/routes_accounting_cases_v2.py app/api/__init__.py \
  tests/test_core_v2_bank_orchestration.py
All checks passed
```

The headless probe covers review/export lifecycle, cross-operation idempotency conflict,
retry-tampering immutability, and evidence supersession/recheck with no LLM or BRAVO API.

On 2026-08-01, an isolated base-compose PostgreSQL container was healthy; the current `test`
image ran `alembic upgrade head` and the focused suite: **7 passed**.

- `tests/test_core_v2_bank_orchestration.py` contributes six tests proving the SQL persistence path
  for create/evidence/checks and cross-department HTTP denial in that container.
- `tests/test_accounting_case_native_rls.py` enables and forces RLS on `accounting_cases_v2`, then
  queries through a non-superuser role. A maker with only
  `accounting_case:create:own_dept` and Department A saw Case A but not Case B. This also proves
  the native GUC uses the most permissive scope already authorized for the request (including
  `create`), rather than incorrectly deriving case visibility only from `read`.

## Limits and next gate

This remains synthetic-only and makes no production, pilot, customer-data, live-bank, BRAVO
execution, or offline-readiness claim. The isolated proof is not a production RLS cutover or an
operational network/credential proof. There is no AccountingCase MCP or worker entry point in this
scope; generic platform MCP/worker two-user/two-department probes therefore remain open and must
not be inferred from these API/SQL tests. WP-05 remains gated on the separate frozen evaluation
work and the applicable platform operational proofs; do not start frontend, Voucher, or Period
Close work from this evidence alone.
