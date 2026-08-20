# BRAVO AI Copilot — current project state

Status: `PLAN 20 DEV HANDOFF READY — FigmaMake-only standalone boundary accepted; implementation and external gates remain open`
Owner: project owner  
As of: 2026-08-19 (runtime/test figures retain their stated 2026-08-02 evidence date)
Evidence window: branch `codex/v2-financial-close-core`; see the dated reproducible commands in
`evidence/v2/V2-DEVELOPER-TRACK-STATUS.md`. Historical baseline hashes below are not a claim that
the current development worktree is clean.

## Executive state

BRAVO retains its existing platform shell (identity, application RLS, retrieval, governed tools,
audit, checkpoints and deployment). Historical draft/approval services are not active product
authority under Plan 20; reusable review controls must be exposed through the new read-only
contracts. The current direction remains a **framework-
independent Conversation Core V2** behind that shell. Its product target is the standalone
**BRAVO Accounting Intelligence** shell with two separately governed modules: Knowledge Chat and
an Accounting Operations Hub (`Công việc AI`). Financial Close is one benchmark family and
possible case template, not the product identity or final objective. ADR-0032 selects
**Reconciliation & Exception Investigator** as the first deep V2 demonstrator. It does not select
a paid pilot by itself. ADR-0033 accepts the owner decision packet and adds two bounded functional
cases: Voucher Evidence & Accounting Review and Period Close Readiness. See
`plan-rebuild/10-FRONTIER-BRAVO-ACCOUNTING-AGENT-PLAN.md`.
It is not approval to keep broad-patching the legacy agent loop, nor to rewrite the entire
platform.

WP-00 is passed for the synthetic demo: a 30-case System A/B baseline is frozen with checksums.
WP-01 synthetic fixture truth is owner-accepted; WP-02 implements the framework-independent
AccountingCase Core V2; and WP-03 implements and golden-tests the LLM-free Bank reconciliation
engine. Plan 16 BF-00 through BF-05 automated exits now pass: Bank business-flow defects were
corrected, Voucher and Period Close use server-authoritative immutable evidence and durable shared
lifecycles, bounded reasoning remains non-mutating, and migration `0020_case_v2_audit` adds the V2
RLS/audit backstops. The owner accepted the FE admission packet and recorded `FE ADMISSION OPEN`
for local synthetic FigmaMake three-case integration. The 24-trajectory blind evaluation and all
production/pilot claims remain open. The Engineering Workbench and frontend tracks remain
independent and are not evidence that conversation quality has improved.

Plan 19 subsequently identified reproducible Knowledge Chat decomposition/routing/evidence defects,
froze a 30-pair synthetic System A/B baseline and established ADR-0034 for Conversation V2
contracts. The owner accepted the synthetic ten-transaction fixture, but independent
accounting/BRAVO SME review and Core V2 implementation remain open. Plan 20/ADR-0035 now select the
current shipped-product boundary: `FigmaMake_UI` only, user-supplied file evidence, no live BRAVO
connector or ERP mutation, and a bounded benchmark-first Artifact Workspace after verified
analysis. Current source has not yet completed that cutover/containment, so this is dev authority
and target architecture, not runtime evidence.

## BRAVO 10 business-flow remediation and FE admission (2026-08-02)

The accounting/domain, API and security council compared the V2 implementation with the BRAVO 10
Accounting, Documents, Purchases, Managements and System guides plus the WP-01 contracts. The
initial audit reproduced false-positive Bank, Voucher and Period Close paths and selected Plan 16.

The developer remediation now provides:

- source-authority enforcement and a three-case business-flow traceability matrix;
- global Bank candidate/conflict handling, truthful reference matching and scope/status/cutoff
  enforcement;
- server-authoritative immutable Voucher and Period Close evidence with durable
  create → evidence → checks → review → export lifecycles;
- a bounded deterministic reasoning fallback that cannot change findings or perform ERP actions;
- case/command/audit RLS plus an append-only audit database backstop at Alembic head
  `0020_case_v2_audit`.

The recorded developer run is `493 passed, 35 skipped, 2 warnings`. The owner accepted the
[FE admission packet](../evidence/v2/V2-BRAVO10-FE-ADMISSION-REVIEW-PACKET-2026-08-02.md) and
[recorded `FE ADMISSION OPEN`](../evidence/v2/V2-BRAVO10-FE-ADMISSION-COUNCIL-DECISION-2026-08-02.md).
This opens Plan 16 BF-06 only; independent SME, live-model, operator, user-time, pilot and
production gates remain deferred.

## Phase-demo topology decision

For the current conversation-quality demo, Keycloak/OIDC is explicitly out of scope. The effective
synthetic single-tenant demo topology must not include `deploy/docker-compose.keycloak.yml`, a
Keycloak container, or an OIDC ingress. It is **not** a production topology and makes no production
identity claim. The existing trusted application identity/RLS shell remains in place for the
demo. ADR-0033 selects a customer-managed single-tenant on-prem data plane as the pilot reference
target. A pilot/production release must still prove customer identity federation, service
identity and resource-level authorization; this does not mandate Keycloak.

This scope reduction does not relax authorization, tenant isolation, draft/approval, audit,
offline-path, credential, or network-ingress invariants. The Keycloak overlay remains reference
material only and must not be combined with the phase-demo topology.

## Verified baseline

| Item | Verified state | Evidence / limit |
|---|---|---|
| Git baseline | Current observed commit `c41255635bee7e594e4b867cf26f5691b98097cc`; remediation worktree is dirty | Dirty state is explicit and contains the admitted V2 remediation/evidence; it is not a clean-baseline claim |
| Alembic | `0020_case_v2_audit` is the single head | Verified through workspace `.venv`, 2026-08-02 |
| Python test suite | 493 passed, 35 skipped, 2 warnings | Admission packet run after migration; skipped/external gates are not inferred as passed |
| Focused containment/evaluation tests | 17 passed, 5 skipped | Owner authorization, answer-guard parity, CAS state, native-RLS, replay/C0/SME/release-gate contracts |
| Markdown documentation | 286 Markdown files inventoried, 0 broken relative-link occurrences | Fresh `scripts/audit_markdown_docs.py` admission audit, 2026-08-02; two exact duplicate groups remain review signals |
| Static lint | Not green repository-wide | `ruff check app tests scripts` reports 10 pre-existing test-file findings; no code was changed in this documentation pass |

The suite emitted two dependency/deprecation warnings (Starlette HTTP 422 alias and
`langchain-community` through RAGAS). They do not fail the suite, but they are maintenance work,
not proof of a clean dependency posture.

## Evidence-backed progress

| Work item | Current state | What it does **not** prove |
|---|---|---|
| Legacy `/api/agent/ask` owner authorization and rate limiting | Implemented and covered by focused tests | Two-user/two-department production probes across HTTP, MCP and worker |
| One final-answer safety/grounding guard for sync and SSE | Implemented and parity-tested | Grounded usefulness or SME quality |
| Consultant state CAS and corrupt-state recovery | Implemented and unit-tested | Correctness under a real concurrent PostgreSQL workload |
| Native Postgres RLS backstop | Migration `0017` and preflight exist; feature is OFF by default | Runtime enforcement: the current owner/superuser connection bypasses RLS until separate non-owner roles and cutover probes are completed |
| Worker/default-credential and Compose containment | Code/config safeguards were added | Effective deployed network exposure, credential rotation, or operational approval |
| A/B capture, C0 arm and SME/release-gate tooling | Code and contract tests exist | An immutable answer/trace baseline, calibrated SME score, or any quality win |
| Conversation/AccountingCase Core V2 three-case backend | Plan 16 BF-00..05 automated exits accepted; all three cases use server-authoritative evidence and durable create/evidence/check/review/export flows; `0020` adds V2 RLS/audit backstops | Independent SME truth, owner-pinned live-model quality, non-owner HTTP/MCP/worker cutover, customer-data, pilot or production claim |
| FigmaMake three-case frontend | `FE ADMISSION OPEN`; candidate typecheck, 4 files/8 tests and production build pass at admission baseline | Integrated API lifecycle, full E2E/a11y/visual evidence, local-demo completion, conversation-quality or release claim |
| BravoGen R0 collection | Complete as black-box behavioral evidence | BravoGen internals or BRAVO knowledge truth |

## Gates still open

No production, security, or quality claim may be made until the following evidence exists:

1. Preserve the WP-00 runtime/credential/RLS/restore evidence as synthetic-demo evidence only;
   it is not a production or pilot authorization.
2. Preserve the frozen 30-case System A/B baseline before changing routing, retrieval, prompts or
   synthesis. It is not a full blind quality verdict.
3. Preserve Financial Close cases as benchmark coverage, add matched Reconciliation & Exception
   Investigator anchors, then add case-specific fixtures/tests for Voucher Review and Period Close
   Readiness. Validate capability-specific evidence contracts and obtain
   reviewer calibration and blind SME evidence before judging Core V2. Benchmark coverage does not
   select the product capability.
4. Independently run frontend typecheck/test/build and the controlled offline/egress smoke before
   making frontend or on-prem readiness claims.

## Historical implementation sequence (completed through WP-03)

1. Use the current clean commit as the named code baseline and record the redacted environment,
   lockfile hashes and effective Compose evidence in a controlled run artifact.
2. Complete the operational containment proofs above. If the required runtime roles, maintenance
   window, credentials or backup target are unavailable, record the gate as blocked rather than
   simulating a pass.
3. Freeze the full matched System A/B anchor set, including the existing Financial Close cases,
   with no further prompt, routing, retrieval or synthesis edits.
4. Apply ADR-0032 to Bank statement ↔ sổ tiền gửi BRAVO: freeze its scope/schema, deterministic
   rules, golden fixtures and SME answer key. Apply accepted packet 11/ADR-0033 to the two bounded
   cases.
5. Only then create the framework-independent Core V2 contracts; implement Bank Reconciliation
   first, then Voucher Evidence Review, then Period Close Readiness behind the same narrow ports.
   BRAVO remains the voucher, accounting-close and reporting engine.

## Current next step

Commit the Plan 19/20/ADR-0035 decision set, then begin Plan 20 WP20-00. Record a clean
implementation baseline and Alembic source head; freeze the machine-readable keep/rename/remove/
defer inventory and obtain a retention decision for historical draft/journal records. Next execute
the FigmaMake production cutover and reversible API/tool containment with negative tests. Do not
start an Office engine, prompt/model migration or new accounting case during this slice.

After WP20-00/01/02 exit, complete the independent SME review still open for the owner-accepted
Plan 19 fixture, implement the minimal file/evidence spine and Conversation V2 contracts, then build
Bank Reconciliation as the first end-to-end file-backed vertical slice. Office delivery begins as a
governed XLSX artifact after verified Bank results and a format-specific fidelity benchmark, not as
a separate general Office Agent.

Plan 18 remains technically demo-complete evidence for the older local synthetic handoff, and Plan
15 still governs deferred external/operator/SME evidence where not superseded. Neither substitutes
for the new Plan 20 containment, independent SME, blind quality or release gates.

## Source of truth and precedence

1. Reproducible code, tests, migrations and runtime evidence override prose claims.
2. This file owns the current snapshot; `docs/AI-REVIEW-MANIFEST.md` owns the bounded review set.
3. Accepted ADRs own existing platform invariants. ADR-0032 selects the primary demonstrator;
   ADR-0033 accepts the three-case scope and owner package. Its pilot target does not supersede
   ADR-0019/0022 until a future real-data ADR and enforcement evidence exist. ADR-0034 owns the
   Conversation V2 contract boundary. ADR-0035 amends the current roadmap to FigmaMake-only,
   file-evidence standalone operation with no BRAVO connector/mutation and a bounded Artifact
   Workspace.
4. The `plan-rebuild/04–12` documents own the original V2 decision design and backlog; Plan 16 owns
   the 2026-08-02 business-flow remediation and FE admission gate; Plan 17 owns the admitted
   FigmaMake three-case frontend execution; Plan 18 owns completion of the two-module local
   internal-demo shell and the Plan 17 handoff exit. Plan 19 owns Knowledge Chat quality
   remediation and frozen-baseline sequencing; Plan 20 owns the current product-completion and dev
   handoff order.
5. `docs/research/**`, `docs/reviews/**`, `docs/work-packages/**`, `plan-rebuild/bravogen-p0/**`,
   `file_system/**` Markdown, and archive directories are retained evidence/reference only. Do
   not treat them as current progress without fresh verification.
