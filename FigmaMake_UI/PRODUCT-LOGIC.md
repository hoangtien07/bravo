# Bravo Agent AI prototype — product logic

Status: executable UX specification; no backend, API, authentication, RLS, or ERP mutation.

## Product boundary

The prototype represents Conversation Core V2 behind a trusted platform shell. Its dogfood scope is one canonical conversation surface and one deep vertical slice: Financial Close Advisor. Evidence, Knowledge, Approval, the Financial Close prerequisite graph, and role-gated Administration are supporting surfaces.

All displayed records are typed illustration fixtures. Exact company, period, version, financial, schema, execution, approval, or verification claims remain unknown unless a fixture explicitly carries matching evidence and the UI labels it as illustration data.

## Canonical state

- `TaskBrief` owns outcome, profile, status, scope, known/missing facts, risk, epoch, and revision.
- `PrerequisiteNode` owns applicability, prerequisites, evidence, missing evidence, responsible role, completion signal, and next safe action.
- `EvidenceRef` distinguishes user-supplied, inferred, verified, conflicting, missing, and stale evidence.
- `DraftItem` owns revision, validation gaps, lifecycle status, evidence references, and append-only visual audit history.
- `QASettings` selects a role, capability, fixture scenario, and UI state without pretending to enforce security.

## Deterministic task rules

1. A new request starts in `scoping` unless its text clearly identifies a Financial Close outcome.
2. A recognized Financial Close request starts `active` with company and accounting period kept explicitly missing.
3. Changing scope updates both shell scope and current task scope, increments task revision, and invalidates previously ready prerequisites.
4. Pause preserves task state; resume returns it to active; cancel preserves history but disables the composer.
5. Switching the real outcome increments `taskEpoch` and clears selected evidence so facts cannot leak from the previous task.
6. `completed` describes completion of advisory work only; it never means an ERP action was executed or verified.

## Financial Close rules

The plan has eight governed groups: scope, source documents, subledger reconciliation, applicable period processes, period-end entries, closing controls, report mappings/opening balances, and reports/variance review.

- A downstream node does not become ready because a user clicked it.
- `ready` requires a completion signal and relevant evidence in the selected fixture.
- `conflict` or `missing_evidence` blocks dependent conclusions.
- `not_applicable` requires an applicability reason.
- Every status exposes a reason, evidence references or missing evidence, and a safe next action where available.

## Draft lifecycle

Allowed review transitions are fail-closed and revision-aware:

| Current state | Action | Next state | Conditions |
|---|---|---|---|
| `ready_for_review` | Approve | `approved` | Expected revision matches; no validation issues; no missing checks |
| `ready_for_review`, `validation_failed` | Request changes | `changes_requested` | Expected revision matches; note is required |
| `ready_for_review`, `validation_failed`, `changes_requested` | Reject | `rejected` | Expected revision matches; reason is required |

All other transitions are ignored. Approved is distinct from exported, externally executed, and verified. The prototype exposes no automatic execution transition.

## Role and capability rules

Navigation is filtered from typed fixture permissions. Profile selection never changes permission. Administration is visible only for the administrator fixture; approval is visible only for roles with the review capability. These are presentation rules for QA, not security enforcement.

Offline or limited capability adds a visible boundary: only approved local evidence may be used and conclusions requiring unavailable sources remain unconfirmed.

## QA state contract

With `?qa=1`, every product screen can be rendered in default, loading, empty, error, permission denied, stale, conflict, success, or offline state. Loading/empty/error/permission boundaries replace the screen; stale/conflict/success/offline add a governed status banner above the real screen.

