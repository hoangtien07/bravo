# BRAVO AI Copilot — current project state

Status: `PLAN READY FOR DEV — implementation remains blocked by containment proof and A/B baseline freeze`
Owner: project owner  
As of: 2026-07-31
Verified against Git: branch `codex/v2-financial-close-core`, commit `24209ab10535aba2f6facc0cc1bdc766e7eac079`, clean worktree before this documentation update

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

The project has completed and tested a code-level P0 containment increment since the previous
snapshot. It has **not** yet frozen a real A/B answer baseline, built the clean Core V2 domain
package, run the 24-trajectory blind evaluation, or passed the production/platform gates. The
Engineering Workbench and frontend prototype tracks remain independent and are not evidence that
conversation quality has improved.

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
| Git baseline | Clean at `24209ab` before this documentation pass | Current branch is `codex/v2-financial-close-core`; this pass changes documentation only |
| Alembic | `0017_native_rls_backstop` is the single head | `python -m alembic heads` |
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
| Conversation/AccountingCase Core V2 three-case demo | ADR-0032/0033 select deep Bank Reconciliation plus bounded Voucher Review and Period Close Readiness; fixtures and clean domain package not started | Accepted design is not implementation or quality evidence |
| BravoGen R0 collection | Complete as black-box behavioral evidence | BravoGen internals or BRAVO knowledge truth |

## Gates still open

No production, security, or quality claim may be made until the following evidence exists:

1. Rotate the previously exposed provider credential; verify effective phase-demo Compose exposes
   only approved ingress, has no Keycloak/OIDC service or ingress, uses non-default database
   credentials, and authenticates Redis.
2. Provision separate non-owner runtime roles, arm native RLS deliberately, and pass negative
   HTTP, MCP and worker probes with a real PostgreSQL environment. Extend native policy coverage
   beyond `chunks` before relying on it as a database backstop.
3. Run clean `0012 -> head` migration, downgrade/upgrade and all security-critical DB integration
   checks without skips; perform an isolated backup/restore drill including private operational
   data.
4. Freeze System A and B answers, traces, model/version, prompts and versioned evidence snapshots before
   changing routing, retrieval, prompts or synthesis. The repository currently contains tooling,
   not a frozen answer artifact.
5. Preserve Financial Close cases as benchmark coverage, add matched Reconciliation & Exception
   Investigator anchors, then add case-specific fixtures/tests for Voucher Review and Period Close
   Readiness. Validate capability-specific evidence contracts and obtain
   reviewer calibration and blind SME evidence before judging Core V2. Benchmark coverage does not
   select the product capability.
6. Independently run frontend typecheck/test/build and the controlled offline/egress smoke before
   making frontend or on-prem readiness claims.

## Next authorized implementation sequence

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
