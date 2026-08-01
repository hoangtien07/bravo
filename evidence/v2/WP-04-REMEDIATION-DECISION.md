# WP-04 remediation decision

Status: `ACCEPTED FOR IMPLEMENTATION`

Date: 2026-08-01
Trigger: read-only security, domain, and API council review of commit `7edcbde`.

## Problem statement

The first WP-04 implementation proved the frozen Bank fixtures can traverse a headless state
machine, but it did **not** prove a safe authorized API. In particular, its process-local command
cache was not bound to an operation/request fingerprint; review changes could occur before a CAS
transition succeeded; review did not approve an exact payload; and the API did not use the
trusted shell's scoped permission vocabulary. The prior status document must therefore not be
used as evidence that WP-04 passed.

## Options considered

| Option | Description | Decision |
|---|---|---|
| A. Patch only the in-memory adapter | Key cache fixes and a demo-only warning, leaving module-global case state and no audit/RLS persistence. | Rejected: still violates the database-backstop and reconstructable-trace invariants for an authorized route. |
| B. Remove the API and keep a headless test harness | Preserve deterministic Bank checks but make WP-04 only a library exercise. | Rejected: does not deliver the required authorized V2 case endpoints. |
| C. Durable shell adapter with immutable commands and review envelopes | Preserve framework-independent Core V2; add SQL persistence, SQL scope predicates, append-only audit references, canonical scoped permissions, and a feature flag. | **Selected**: smallest option that resolves the council blockers without widening Bank scope or rebuilding BRAVO. |

## Selected design and invariants

1. Domain truth remains framework/database free. SQL, FastAPI, audit, and fixture I/O remain
   adapters outside `app/core_v2` contracts/state machine.
2. Every mutation records a command `(case, operation, idempotency_key, request_hash)` before its
   visible outcome. A repeated equal request returns the recorded outcome; a mismatched request
   receives a conflict before it can change any case/review runtime data.
3. Bank evidence requires exactly the current `bank_statement` and `bravo_bank_ledger` snapshot
   types. A permitted same-source supersession invalidates results, review, draft, and approval,
   then forces a fresh check.
4. The maker creates the immutable draft payload/hash after deterministic checks. An independent
   checker records a typed review decision and approves that exact draft hash. Export requires the
   matching non-stale review/approval envelope and states that BRAVO did not execute anything.
5. API authorization uses scoped trusted-shell permissions (`accounting_case:*:own_dept|all`), not
   ad-hoc bare strings. Creator ownership is metadata, not an authorization bypass after
   department access is revoked.
6. The route is feature-flagged off by default. Enabling it still proves only the synthetic demo;
   native RLS activation and runtime HTTP/MCP/worker probes remain separately recorded gates.

## Verification decision

The remediation is not complete until focused tests demonstrate: cross-operation idempotency
conflict; retry/stale-review immutability; same-department/no-capability denial; maker/checker
separation and exact payload binding; evidence supersession/recheck; SQL-scoped list/get; and
explicit `artifact produced; BRAVO did not execute anything.` output.
