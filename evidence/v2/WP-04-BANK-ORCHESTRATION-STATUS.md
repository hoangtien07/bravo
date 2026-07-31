# WP-04 Bank orchestration status

Status: `IMPLEMENTED FOR SYNTHETIC, SINGLE-PROCESS DEMO`

Baseline at start: clean `9998d5a9a4b1f0c3b020fcd0bddbb39e5cf8ab69` on
`codex/v2-financial-close-core`. The documented pre-handoff Core V2 baseline was `3342168`;
`9998d5a` adds the WP-04 handoff documentation only. No secret store was read or copied.

## Delivered

- `SyntheticBankEvidenceSource` accepts only the frozen WP-01 bank fixture pack and its exact
  `ScopeKey`; it does not accept arbitrary paths, live BRAVO resource IDs, or a BRAVO API.
- Headless orchestration composes scope lock, two evidence snapshots, WP-03 deterministic checks,
  derived findings, reviewer dispositions, and a payload/evidence-hash-bound export artifact.
- Provisional authorized routes are under `/api/v2/accounting-cases`. Mutations require a server
  identity capability, expected revision, and idempotency key. Case access is owner or
  department-scoped; review/export require a reviewer/admin role and maker self-review is denied.
- The export payload states exactly: `artifact produced; BRAVO did not execute anything.` Trace
  output retains snapshot/result references and hashes, not raw fixture rows.

## Verification

Run on 2026-07-31 with `.venv\\Scripts\\python.exe`:

```text
pytest -q -p no:cacheprovider tests/test_core_v2_case_state.py \
  tests/test_core_v2_bank_engine.py tests/test_core_v2_bank_orchestration.py
14 passed

ruff check app/core_v2/synthetic_bank_adapter.py app/core_v2/bank_orchestration.py \
  app/api/routes_accounting_cases_v2.py app/api/__init__.py \
  tests/test_core_v2_bank_orchestration.py
All checks passed
```

The HTTP probe covers creation, evidence, checks, and a foreign-user/different-department `403`.
The headless probe covers the full review/export lifecycle with no LLM or BRAVO API.

## Limits and next gate

This is a process-local synthetic demonstrator adapter, not durable multi-worker persistence or a
native-RLS database backstop. It makes no production, pilot, customer-data, live-bank, BRAVO
execution, or offline-readiness claim. WP-05 remains gated on this focused verification plus the
separate frozen evaluation work; do not start frontend, Voucher, or Period Close work from this
evidence alone.
