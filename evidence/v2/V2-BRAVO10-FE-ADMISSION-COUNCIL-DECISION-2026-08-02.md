# V2 BRAVO 10 FE admission council decision

Status: `FE ADMISSION OPEN — LOCAL SYNTHETIC FIGMAMAKE INTEGRATION ONLY`

Date: 2026-08-02  
Decision maker: project owner  
Owner confirmation: `hãy tự ghi FE ADMISSION OPEN, tôi xác nhận đồng ý`

## Decision

Council accepts the developer evidence in the
[FE admission review packet](V2-BRAVO10-FE-ADMISSION-REVIEW-PACKET-2026-08-02.md) and the
[business-flow traceability matrix](V2-BRAVO10-BUSINESS-FLOW-TRACEABILITY-MATRIX-2026-08-02.md).
Plan 16 BF-00 through BF-05 automated exits are accepted for the purpose of starting BF-06.

`FE ADMISSION OPEN` authorizes development in `FigmaMake_UI/` for the local synthetic
three-case Accounting Operations Hub:

1. Bank Reconciliation — primary/deep.
2. Voucher Evidence & Accounting Review — functional/bounded.
3. Period Close Readiness — functional/bounded.

The candidate frontend may consume the existing same-origin trusted API/auth/RLS shell and the
current durable `/api/v2/accounting-cases` lifecycle. `frontend-react/` remains unchanged as the
functional comparator and rollback shell.

## Required frontend boundary

- Render backend-owned scope, evidence, deterministic results, findings, review state and export
  artifact; never recalculate or upgrade an accounting verdict in the browser.
- Carry server revision, idempotency key, payload hash, evidence hash, result hash and review hash
  exactly as required by the API.
- Treat `403` as denied, `409` as a revision/idempotency conflict, `422` as invalid input and
  disabled capability `404` as unavailable; none may be rendered as an empty or successful case.
- Cover missing, stale, superseded, conflicted, abstained, denied, unresolved and failed states.
- Preserve maker-checker. A maker cannot review their own case, and export remains a generated
  artifact, never evidence that BRAVO executed a posting, payment, close, report, lock or ledger
  change.
- Do not use the legacy `/preview/voucher-review` or `/preview/period-close-readiness` routes as
  the functional UI path.
- Do not add or change backend contracts merely to satisfy a mock screen. Record a contract gap
  and obtain a separate approval before any backend or migration change.

## Allowed completion claim

After the frontend plan and its checks pass, the strongest allowed claim is:

> Local synthetic three-case developer demo ready for human evaluation.

This decision does not establish independent SME acceptance, live-model quality, reviewer-time
improvement, non-owner HTTP/MCP/worker operator cutover, customer-data permission, paid-pilot
readiness, production identity/topology, on-prem readiness or production readiness.

## Execution authority

The implementation sequence, UI contract, work packages, verification matrix, stop conditions and
handoff are governed by
[Plan 17 — FigmaMake UI three-case frontend implementation](../../plan-rebuild/17-FIGMAMAKE-UI-THREE-CASE-FE-IMPLEMENTATION-PLAN.md).
Plan 09 remains a historical design/productization input where Plan 17 does not replace it.

