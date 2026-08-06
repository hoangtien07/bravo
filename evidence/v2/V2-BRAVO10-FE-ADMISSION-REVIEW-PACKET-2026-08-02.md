# FE admission review packet — Plan 16 automated exits

Status: `ACCEPTED BY OWNER — FE ADMISSION OPEN`

Date: 2026-08-02

Decision record:
[V2 BRAVO 10 FE admission council decision](V2-BRAVO10-FE-ADMISSION-COUNCIL-DECISION-2026-08-02.md)

Owner confirmation: `hãy tự ghi FE ADMISSION OPEN, tôi xác nhận đồng ý`

## Council outcome

The owner accepted the reproducible developer evidence below and issued the separate decision
`FE ADMISSION OPEN` for **local synthetic FigmaMake integration only**, with `frontend-react` kept
as the unchanged comparator and rollback shell. This packet does not claim SME acceptance, model
quality, customer-data permission, operator cutover, pilot readiness, or production readiness.

## Corrective result

| Plan 16 gate | Corrective evidence | Automated result |
|---|---|---|
| BF-00 source authority | Manifest requires authority metadata for the BRAVO versioned corpus; B8R4 KQPT documents remain B8R4/draft/unknown scope; exact-claim filter requires matching approved version/scope | manifest and exact-claim tests pass |
| BF-00 traceability | [three-case traceability matrix](V2-BRAVO10-BUSINESS-FLOW-TRACEABILITY-MATRIX-2026-08-02.md) maps scope/evidence/checks to guide sources or explicit synthetic policies | reviewed as versioned developer artifact |
| BF-01 Bank | Global candidate graph preserves conflicts, exact matching compares references, scope/status/cutoff gates apply, review is typed and hash-bound | deterministic/held-out/orchestration tests pass |
| BF-02 Voucher | Server-authoritative immutable synthetic fixture, duplicate/tax/three-way/master/account/dimension checks and durable lifecycle; caller facts cannot create pass | direct and HTTP/DB create → evidence → checks → review → export pass |
| BF-03 Period | Server-authoritative prerequisite/status/approval fixture, empty/foreign/stale paths fail closed, durable lifecycle | direct and HTTP/DB create → evidence → checks → review → export pass |
| BF-04 bounded reasoning | Typed deterministic fallback cannot post/pay/close/lock/run SQL/widen scope or alter findings | adversarial reasoning contract tests pass; no live model asserted |
| BF-05 RLS/audit | cases, commands and V2 audit are scope-controlled; audit is append-only by database trigger; forced-RLS probe passes | migration `0020_case_v2_audit`; native RLS tests pass |

## Runtime evidence

- PostgreSQL local container healthy on host port `55432`; database migration head:
  `0020_case_v2_audit`.
- Full suite run after migration: `493 passed, 35 skipped, 2 warnings`.
- The full run includes the new Voucher and Period HTTP/DB tests and the native RLS/audit test.
- Fixture hashes are frozen in
  [`tests/fixtures/core_v2/wp01/SHA256SUMS`](../../tests/fixtures/core_v2/wp01/SHA256SUMS)
  and [`manifest.json`](../../tests/fixtures/core_v2/wp01/manifest.json).

## Admission scope and frontend handoff constraints

If council opens admission, FE may consume only the existing V2 API/state contracts for the three
functional synthetic cases. Screens must render scope, evidence, findings, review and export; and
must cover missing, stale, superseded, conflict, abstained, denied and unresolved states. The UI
must not infer an accounting result, create a BRAVO identifier, or claim BRAVO executed a posting,
payment, close, lock, report, or ledger change.

`frontend-react` remains the rollback shell. FigmaMake productization must still complete its
typecheck, unit, E2E, accessibility, visual and production-build checks before any local-demo
completion claim.

## Deferred external gates

- independent accounting/BRAVO SME approval of synthetic truth;
- owner-pinned live model record and model-quality evaluation;
- non-owner HTTP/MCP/worker operator probes;
- reviewer-time baseline, real-user evidence, customer-data permission, pilot and production gates.
