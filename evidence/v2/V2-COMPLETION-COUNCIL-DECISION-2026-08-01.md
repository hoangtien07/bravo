# V2 completion council decision

Status: `ACCEPTED EXECUTION SEQUENCE — EXTERNAL EVIDENCE GATES OPEN`

Date: 2026-08-01
Scope: completion of the accepted **synthetic three-case demonstrator** in ADR-0033 and
`plan-rebuild/12-THREE-CASE-DEMO-DEV-BACKLOG.md`. This is explicitly not a pilot or production
plan.

## Developer-track amendment

The owner authorized a developer-completion track that defers real-user and blind-SME testing at
development time. Council accepts this only with two explicit milestones:

1. **Developer-complete synthetic demonstrator:** typed contracts, deterministic checks, bounded
   reasoning guards, UI, fixtures, automated tests and reproducible synthetic evidence are
   complete.
2. **Evaluation/release acceptance:** operator runtime proof, independent SME truth and blind
   review, user-time baseline, and OD-09 evaluation are still required. No quality, usability,
   security cutover, pilot or production claim may use milestone 1 as a substitute.

This permits the engineering order `contract -> deterministic backend -> bounded reasoning -> UI
-> synthetic end-to-end tests` without waiting for people to test. It does not permit UI contracts
to be invented independently of the backend, nor permit an LLM or UI action to mutate accounting
truth.

## Council conclusion

The council compared three completion scopes:

| Option | Decision | Reason |
|---|---|---|
| Bank-only safety milestone | Not selected as V2 completion | Useful intermediate milestone, but conflicts with accepted OD-08 unless the owner amends the three-case scope. |
| Synthetic three-case demonstrator | **Selected** | Matches ADR-0033: a deep Bank case followed by bounded Voucher Review and Period Close Readiness, using the shared Core V2. |
| Pilot/real-data readiness | Rejected for this plan | OD-10 requires a design partner, real-data policy/ADR, identity, egress, retention, recovery and support authority not present in this workspace. |

The implementation sequence is Bank-first and fail-closed. Do not parallelize a new Core, frontend
delivery, or secondary-case implementation ahead of the Bank quality gate.

## Selected execution sequence

1. **WP-00 operational containment evidence.** Use a controlled isolated synthetic deployment,
   non-owner runtime role and armed native RLS to run two-user/two-department HTTP, generic MCP and
   worker probes where those shared entry points apply. Also capture controlled ingress/credential,
   backup/restore, rollback and offline/egress evidence. The existing WP-04 direct SQL native-RLS
   probe remains valuable but is not a production cutover proof.
2. **Freeze the Bank evaluation packet.** Pin the approved synthetic-only model/version and budget;
   freeze matched anchors, expected deterministic outputs, must-not claims, trace/lineage contract,
   blind rubric and sealed held-out process. Preserve the existing System A/B artifact unchanged.
3. **WP-05 Bank conversation and evaluation.** Implement only a narrow typed `ReasoningPort` that
   consumes immutable Bank findings and may ask a high-information question, explain a finding,
   provide a mapping candidate, narrate an investigation, or abstain. It may not modify monetary
   values, classification, policy, review, approval or export state. Run the frozen A/B/C and
   ablation protocol; stop or narrow if OD-09 fails.
4. **WP-06 Bank UX.** After the Bank quality/safety gate, implement the typed Accounting Work inbox
   and shared case page, with explicit synthetic/stale/missing/superseded/abstained labels and no
   implied execution.
5. **WP-07 then WP-08.** Freeze each secondary case's policy, fixture, golden and held-out truth
   before code. Implement Voucher Evidence Review, then Period Close Readiness, reusing Core V2 and
   never rebuilding BRAVO posting, close calculations, reports or period lock.
6. **WP-09 then WP-10.** Add reproducible config-as-code and the explicitly non-functional
   Governance/Integration mock; run integrated security, frontend, A/B/C/D, blind SME, reviewer
   baseline and release evidence. Stop at the synthetic demonstrator.

## Blocking authority and evidence

These are real gates, not missing code to simulate:

| Gate | Required authority/evidence | Status |
|---|---|---|
| Runtime containment | Operator-controlled non-owner role, RLS arm/rollback, runtime HTTP/MCP/worker, ingress/credential and restore window | `BLOCKED — operator authority required` |
| Bank model/evaluation | Owner-approved concrete model/version, synthetic egress policy and immutable evaluation run configuration | `BLOCKED — owner/model authority required` |
| Bank quality verdict | Two independent qualified SMEs, calibration, sealed held-out answer key, blind scoring and comparable manual baseline | `BLOCKED — SME/user participation required` |
| Voucher/Close truth | Approved synthetic policy and golden/held-out fixtures for each bounded case | `BLOCKED — owner/SME truth required` |
| Pilot | OD-10 design-partner, customer-data and operational evidence | `DEFERRED — out of demonstrator scope` |

If an authority or controlled environment is unavailable, record the particular gate as blocked.
Do not enable real data, direct BRAVO DB access, autonomous mutation, unbounded model egress, or
claim a quality/security/pilot pass from synthetic structural tests.

## Decision log and follow-up

- The V2 completion target is the accepted synthetic three-case demonstrator, not a Bank-only
  endpoint and not pilot readiness.
- Generic MCP/worker proof is treated as applicable to the trusted shared platform until an owner
  records a specific non-applicability decision. It is not inferred from the AccountingCase SQL
  probe.
- The feature flag remains off by default outside an explicit synthetic demonstration environment.
- The next implementation handoff starts only after the first two gates above have reproducible
  evidence. Its handoff must name the immutable fixture/evaluation hashes, model/version and the
  exact remaining blocker.
