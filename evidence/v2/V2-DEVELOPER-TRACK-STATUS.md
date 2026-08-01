# V2 synthetic developer-track status

Status: `IN PROGRESS — INTEGRATED AUTOMATION PARTIAL, HUMAN/OPERATOR GATES DEFERRED`

## Built and automated

- Bank: durable synthetic case shell, scoped API, deterministic reconciliation, hash-bound
  maker/checker review/export, read-only bounded conversation and Accounting Work UI. The UI sends
  the server revision and a fresh idempotency key for frozen-case creation, evidence, checks,
  review and artifact export; review/export tests also bind every current disposition and envelope
  hash. Authorization and transition decisions remain in the API/database.
- Voucher: typed synthetic evidence, deterministic total/duplicate/three-way/lineage checks and a
  read-only API/UI workbench. It preserves missing inputs for the API to return `abstain`; it does
  not post a voucher or create a parallel ledger.
- Period Close: typed prerequisite/reconciliation inputs, deterministic fail-closed readiness
  projection and a read-only API/UI workbench. It renders every blocker; it does not calculate
  close, generate reports or lock a period.
- Demo configuration is versioned and fail-closed to synthetic-only with model egress denied until
  the owner pins a model/version. Runtime activation now requires both
  `ACCOUNTING_CASE_V2_ENABLED=true` and the versioned
  `ACCOUNTING_CASE_V2_DEMO_CONFIG`; boot rejects a missing, invalid, non-synthetic, or
  capability-disabled manifest. Bank/Voucher/Period routes separately enforce their named manifest
  capability flags, so a UI/API caller cannot widen an unavailable feature.
- The FigmaMake prototype and `frontend-react` have an Accounting Work surface governed by the
  contract-first handoff. The FigmaMake Bank frame now mirrors the controlled evidence/check/
  reviewer-disposition/artifact sequence, while remaining a non-executing visual prototype.

## Reproducible developer verification

Run on 2026-08-01:

```text
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider [focused Core V2 tests]
44 passed, 1 skipped

.venv\Scripts\ruff.exe check app/core_v2 app/adapters/accounting_case_store.py \
  app/api/routes_accounting_cases_v2.py [focused Core V2 tests]
All checks passed

.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider \
  tests/test_core_v2_demo_config.py tests/test_boot.py tests/test_core_v2_developer_track.py
20 passed

.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider \
  tests/test_core_v2_demo_config.py tests/test_core_v2_secondary_preview_http.py \
  tests/test_core_v2_bank_orchestration.py
12 passed, 1 skipped (the durable Bank HTTP proof requires reachable PostgreSQL)

cd frontend-react
npm.cmd test -- --run
6 files, 13 tests passed
npm.cmd run build
Production build passed

cd FigmaMake_UI
pnpm.cmd test -- --run src/test/accountingWork.test.tsx
4 files, 8 tests passed
pnpm.cmd run typecheck
Typecheck passed
pnpm.cmd run build
Production build passed
```

The skipped backend test needs reachable PostgreSQL for the durable Bank HTTP path. It has separate
isolated-container evidence in `WP-04-BANK-ORCHESTRATION-STATUS.md`; this local run is not a
replacement. Frontend build emits existing large-chunk warnings and React Router future-flag
warnings; neither is treated as a release acceptance.

### 2026-08-02 controlled local durable-HTTP probe

The Docker operator context can read Compose and has the `pgvector/pgvector:pg16` image. The
repository-local Postgres container could not start because `127.0.0.1:5432` is already held by a
non-Compose `postgres` process; the test harness also reports its configured PostgreSQL as
unreachable. The temporary Compose container and network were removed with `docker compose down`
without a volume removal. No `.env` value or credential of the unrelated process was read or
tried. Therefore `test_http_routes_enforce_server_identity_scope_and_complete_headlessly` remains
an explicit local skip, not a passed E2E result. An operator must provide an approved isolated
database endpoint or free/map the local port before rerunning it.

## Known developer-track boundary

Only Bank currently has durable persisted case/review/export lifecycle. Voucher and Period Close
are deliberately preview-only until their complete synthetic policy, golden fixture and review
envelope semantics are approved. They must not be represented as a completed persisted workflow.
This avoids adding a generic persistence abstraction from unspecified accounting policy.

The configuration boot guard is a developer/synthetic containment control. It is not a substitute
for an operator-managed non-owner RLS cutover, a model-owner decision, or production deployment
approval.

## Deferred, not passed

- independent SME truth, sealed held-out answer key and blind review;
- reviewer-time/manual baseline;
- non-owner operator runtime/RLS cutover, generic MCP/worker and restore/egress proof;
- real data, pilot, deployment and production claims.
