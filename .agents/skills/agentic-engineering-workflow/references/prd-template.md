# Product Requirements Document

Use this template for a large feature after alignment. Remove instructions that do not belong in the final artifact.

## Document control

- Title:
- Status: Draft | Aligned | Approved | Superseded
- Owner:
- Reviewers:
- Last updated:
- Related decisions/issues:

## Problem statement

Describe the observed problem, affected actors, current evidence, and why it matters now. Separate verified facts from hypotheses.

## Goals and measures

- Goal:
- Observable success measure:
- Baseline or comparison:

## Non-goals

- Explicitly excluded behavior:
- Deferred work:

## Actors and user stories

For each actor, state the outcome and authorization scope.

- As a …, I need …, so that …

## Shared design concept

Summarize the intended end state, key constraints, and confirmed decisions without reproducing the interview.

## Business and system flows

Describe the happy path, alternate paths, approval boundaries, and state transitions. Add a diagram only when it clarifies dependencies or state.

## Business rules

List deterministic rules, invariants, and evidence requirements. Identify the source or decision owner for each consequential rule.

## Data and migration

- Data read/written:
- Ownership, retention, privacy, and tenant scope:
- Schema/state changes:
- Backfill or migration sequence:
- Compatibility and rollback:

## Security and authorization

- Actors and permissions:
- Enforcement point and database backstop:
- Entry points and negative isolation cases:
- Secret/PII/egress constraints:
- Draft, approval, and execution boundaries:

## Failure modes and recovery

For each material failure, state detection, user-visible behavior, retry/idempotency, containment, and recovery.

## Observability

- Events, logs, metrics, traces, and audit records:
- Privacy minimization:
- Alert or operational threshold:

## Acceptance criteria

Use observable, testable statements. Include negative and boundary behavior.

- Given … when … then …

## Testing and evaluation strategy

- Unit:
- Integration/database:
- Contract/API:
- Security and isolation:
- Migration/rollback:
- UI/E2E/visual QA:
- Performance or quality benchmark:

## Rollout and rollback

- Feature gate/canary sequence:
- Compatibility window:
- Stop conditions:
- Rollback procedure and data implications:

## Open questions

Record only unresolved questions that can change scope, design, safety, or acceptance.

## Confirmed decisions

| Decision | Owner | Date | Consequence |
|---|---|---|---|
|  |  |  |  |

## Evidence and source references

| Claim or requirement | Source | Strength/limitations |
|---|---|---|
|  |  |  |
