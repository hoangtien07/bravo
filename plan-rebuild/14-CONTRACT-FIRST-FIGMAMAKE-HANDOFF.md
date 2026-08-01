# V2 contract-first design and development handoff

Status: `ACTIVE — BACKEND/AGENT FIRST, FIGMAMAKE DESIGN FOLLOWS FROZEN CONTRACTS`

Date: 2026-08-01
Authority: owner developer-track amendment in
`evidence/v2/V2-COMPLETION-COUNCIL-DECISION-2026-08-01.md`.

## Purpose

This handoff governs the next Design + Development work. `FigmaMake_UI` remains the visual
prototype source, while `frontend-react` remains the production integration shell. Do not deploy
the current prototype as a completed product, and do not invent API behavior from screens.

## Selected flow

```text
Business policy + synthetic fixtures
  -> typed backend contracts and deterministic checks
  -> bounded read-only agent/reasoning contract
  -> versioned API examples
  -> FigmaMake_UI design states and interaction specification
  -> frontend-react integration against the real API
  -> synthetic E2E/visual/a11y tests
  -> deferred human/SME/operator evaluation gates
```

The design work may prepare layout, tokens and navigation in parallel, but a case interaction is
not approved for implementation until its API grammar, authorization action, state transition,
evidence/lineage fields and failure/abstention behavior are named below.

## Synthetic runtime activation

The V2 API remains off by default. A developer demo must explicitly set
`ACCOUNTING_CASE_V2_ENABLED=true` and
`ACCOUNTING_CASE_V2_DEMO_CONFIG=file_system/core_v2_synthetic_demo.yaml` (or another valid,
versioned synthetic manifest). The boot guard rejects a missing, malformed, non-synthetic, or
capability-disabled manifest. This only authorizes a synthetic developer demo; it does not enable
model egress, use real data, or replace the deferred operator/release gates.

## Current contract inventory

| Capability | Backend status | Design input | UI integration status |
|---|---|---|---|
| Bank case lifecycle | Typed V2 API, durable synthetic case store, maker/checker/export boundary | `GET/POST /api/v2/accounting-cases`; evidence, findings, state, revision, hash/approval fields | Accounting Work implements frozen-case creation, evidence/check actions, reviewer dispositions and review-artifact export; server retains authorization/state authority |
| Bank conversation | Read-only bounded endpoint | `POST /api/v2/accounting-cases/{case_id}/conversation` with `question`; reply has `kind`, text, finding/evidence/rule references and `mutates_case=false` | Integrated in case dossier |
| Voucher Review | Read-only synthetic deterministic preview | `POST /api/v2/accounting-cases/preview/voucher-review`; total, duplicate, three-way and lineage result states; missing evidence is `abstain` | No persisted case/review UI yet — do not design a posting action |
| Period Close Readiness | Read-only synthetic deterministic preview | `POST /api/v2/accounting-cases/preview/period-close-readiness`; prerequisite, freshness and material reconciliation blockers | No persisted case/review UI yet — do not design a close action |

## Required screen behavior

Every case page must include Scope, Evidence, Findings, Recommendation/Explanation, Draft action
and Review/Audit sections. It must render loading, empty, denied, error, missing, stale,
superseded, abstained and review-required states. Labels must distinguish synthetic, verified,
inferred and missing data. “Export” says artifact produced and never says BRAVO executed anything.

For the current Bank contract, UI writes must send the server revision and idempotency key. UI
authorization is presentation only; the API/database remains authoritative. A UI may not calculate
amounts, classify results, approve its own draft, or claim an ERP operation succeeded.

## Handoff package before each FigmaMake_UI change

The backend/agent implementer supplies:

1. OpenAPI/route grammar and typed request/response examples with synthetic IDs only.
2. State transition diagram, role/action matrix and expected revision/idempotency behavior.
3. Fixture pack version/hash, deterministic rule IDs, evidence labels and must-not claims.
4. Rendering matrix for success, missing, stale, superseded, abstained, denied and conflict cases.
5. Contract tests proving the example payloads and a clear list of unavailable interactions.

The designer returns frame states and interaction notes, not new backend semantics. The frontend
implementer maps those frames to `frontend-react` API types and adds E2E/a11y/visual checks.

## Sequencing

1. Extend the Bank automated fixtures/evaluation and use the exact controls above in FigmaMake frames.
2. Publish/update the Bank handoff package from those exact contracts.
3. Finish Voucher policy/fixture/API contract, then its screens; do not add posting.
4. Finish Period Close prerequisite policy/API contract, then its screens; do not add close engine.
5. Add integrated synthetic evidence.

## Deferred gates

Blind SME review, reviewer-time baseline, non-owner operational RLS cutover, generic MCP/worker
runtime probes and all pilot/production decisions remain deferred. Their absence is recorded as a
gate, never rendered as a completed UI state or release claim.
