# Independent Review Checklist

Review the supplied requirements, acceptance criteria, diff, tests, and relevant code. Report findings by severity with precise evidence; do not reconstruct the implementation journey.

## 1. Requirements

- Does the change satisfy every confirmed requirement and acceptance criterion?
- Are assumptions, non-goals, and unresolved decisions visible?
- Did scope expand beyond the selected vertical slice?

## 2. Tests

- Do tests assert desired behavior rather than mirror implementation details?
- Is there credible evidence that new tests failed for the intended reason before the fix?
- Are negative, boundary, concurrency, retry, and recovery cases proportionate to risk?
- Were tests weakened, skipped, or acceptance criteria redefined?

## 3. Correctness

- Are state transitions, invariants, error paths, idempotency, and concurrency correct?
- Can partial failure leave inconsistent state or a misleading success response?
- Does the implementation match existing conventions and avoid shallow, fragmented modules?

## 4. Security

- Is authorization enforced at every entry point and backed by the data layer where required?
- Can tenant data leak through queries, caches, logs, errors, citations, workers, MCP, or session reuse?
- Are secrets, PII, egress, draft/approval, and execution boundaries preserved?

## 5. Data and migrations

- Are schema changes reversible or explicitly one-way with approval?
- Are backfill, compatibility, retention, constraints, and downgrade/upgrade behavior covered?
- Can old and new application versions coexist for the rollout window?

## 6. API compatibility

- Are public contracts, validation, status codes, streaming/events, and clients backward compatible as agreed?
- Are timeouts, retries, idempotency, and structured errors defined?

## 7. Frontend behavior

- Are loading, empty, error, success, disabled, and responsive states handled?
- Do component/E2E tests and rendered visual inspection support UI claims?
- Are accessibility and authorization-dependent states correct?

## 8. Observability

- Can operators distinguish success, failure, retry, partial completion, and policy denial?
- Are logs, metrics, traces, and audits useful without exposing sensitive data?

## 9. Documentation

- Is the current source of truth updated?
- Are superseded plans marked and operational/runbook changes documented?
- Do claims cite matching code, test, migration, or runtime evidence?

## 10. Residual risks

- List unrun checks, remaining findings, rollout risks, and required human QA.
- Confirm that blockers remain open until every required path has closure evidence.
- Give a final verdict: approve, approve with tracked follow-ups, or block.
