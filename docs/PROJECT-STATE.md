# BRAVO AI Copilot — current project state

Status: `V2 SYNTHETIC THREE-CASE PLAN ACCEPTED — operational and evaluation gates remain open`
Owner: project owner  
As of: 2026-08-02
Evidence window: branch `codex/v2-financial-close-core`; see the dated reproducible commands in
`evidence/v2/V2-DEVELOPER-TRACK-STATUS.md`. Historical baseline hashes below are not a claim that
the current development worktree is clean.

## Executive state

BRAVO retains its existing platform shell (identity, application RLS, retrieval, tools, draft
approval, audit, checkpoints and deployment). The current direction remains a **framework-
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
engine. WP-04 has a remediated synthetic orchestration/API implementation, including durable
case-command shell migrations and isolated SQL/HTTP/native-RLS runtime proof. The
24-trajectory blind evaluation and all production/pilot claims remain open. The Engineering
Workbench and frontend prototype tracks remain independent and are not evidence that conversation
quality has improved.

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
| Git baseline | Remediation worktree follows `7edcbde` | Current branch is `codex/v2-financial-close-core`; see WP-04 remediation decision/evidence |
| Alembic | `0019_case_v2_defaults` is the single head | Fresh isolated PostgreSQL migration through head, 2026-08-02 |
| Python test suite | 404 passed, 41 skipped | `python -m pytest -q -p no:cacheprovider`, 2026-07-24; skipped tests are not a DB/production pass |
| Focused containment/evaluation tests | 17 passed, 5 skipped | Owner authorization, answer-guard parity, CAS state, native-RLS, replay/C0/SME/release-gate contracts |
| Markdown documentation | 259 Markdown files inventoried, 0 broken relative-link occurrences | `docs/documentation/MARKDOWN-INVENTORY.md`; 254 tracked plus plans 10–12 and ADR-0032/0033 untracked during this documentation pass; two intentional import duplicates remain review signals |
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
| Conversation/AccountingCase Core V2 three-case demo | WP-01 owner-accepted synthetic schemas/fixtures; WP-02 core contracts/CAS/state machine; WP-03 deterministic Bank engine; WP-04 durable Bank command/review shell, SQL/HTTP authorization, isolated native-RLS probe; Bank UI/reasoning and read-only typed Voucher/Period previews are on the developer track | Blind quality claim, customer-data authorization, production/operational claim, generic MCP/worker probes, and persisted Voucher/Period lifecycle |
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

Continue the selected Bank-first synthetic three-case sequence in
`evidence/v2/V2-COMPLETION-COUNCIL-DECISION-2026-08-01.md`. The developer track has Bank
conversation/UI workflow controls, read-only Voucher/Period previews and a synthetic runtime
manifest; next close the Bank automated fixtures/evaluation, contract-first FigmaMake states and
synthetic integration evidence. Keep legacy endpoints unchanged. Do not simulate operator, owner,
SME, user, customer or pilot evidence when the required authority is unavailable.

For developer completion only, the owner has authorized implementation and automated synthetic
end-to-end checks through the UI before real-user or blind-SME testing. The evaluation/release
gates remain deferred and must never be reported as passed from this developer track.

The next design/dev handoff is contract-first: see
`plan-rebuild/14-CONTRACT-FIRST-FIGMAMAKE-HANDOFF.md`. `FigmaMake_UI` is a design/prototype input;
`frontend-react` integrates only frozen backend/agent contracts and their synthetic examples.
The reproducible developer-track boundary and deferred gates are recorded in
`evidence/v2/V2-DEVELOPER-TRACK-STATUS.md`.

## Source of truth and precedence

1. Reproducible code, tests, migrations and runtime evidence override prose claims.
2. This file owns the current snapshot; `docs/AI-REVIEW-MANIFEST.md` owns the bounded review set.
3. Accepted ADRs own existing platform invariants. ADR-0032 selects the primary demonstrator;
   ADR-0033 accepts the three-case scope and owner package. Its pilot target does not supersede
   ADR-0019/0022 until a future real-data ADR and enforcement evidence exist.
4. The `plan-rebuild/04–12` documents own the V2 decision design, dev backlog and gates.
5. `docs/research/**`, `docs/reviews/**`, `docs/work-packages/**`, `plan-rebuild/bravogen-p0/**`,
   `file_system/**` Markdown, and archive directories are retained evidence/reference only. Do
   not treat them as current progress without fresh verification.
