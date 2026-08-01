# V2 synthetic developer-track status

Status: `IN PROGRESS — INTEGRATED AUTOMATION PARTIAL, HUMAN/OPERATOR GATES DEFERRED`

## Built and automated

- Bank: durable synthetic case shell, scoped API, deterministic reconciliation, hash-bound
  maker/checker review/export, read-only bounded conversation and Accounting Work UI.
- Voucher: typed synthetic evidence, deterministic total/duplicate/three-way/lineage checks and a
  read-only API/UI preview. It does not post a voucher or create a parallel ledger.
- Period Close: typed prerequisite/reconciliation inputs, deterministic fail-closed readiness
  projection and a read-only API/UI preview. It does not calculate close, generate reports or lock
  a period.
- Demo configuration is versioned and fail-closed to synthetic-only with model egress denied until
  the owner pins a model/version.
- The FigmaMake prototype and `frontend-react` have an Accounting Work surface governed by the
  contract-first handoff.

## Known developer-track boundary

Only Bank currently has durable persisted case/review/export lifecycle. Voucher and Period Close
are deliberately preview-only until their complete synthetic policy, golden fixture and review
envelope semantics are approved. They must not be represented as a completed persisted workflow.
This avoids adding a generic persistence abstraction from unspecified accounting policy.

## Deferred, not passed

- independent SME truth, sealed held-out answer key and blind review;
- reviewer-time/manual baseline;
- non-owner operator runtime/RLS cutover, generic MCP/worker and restore/egress proof;
- real data, pilot, deployment and production claims.
