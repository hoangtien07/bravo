# BRAVO AI Copilot — current project state

Status: `IN_PROGRESS — containment implementation verified; R1 baseline freeze and Core V2 slice remain open`
Owner: project owner  
As of: 2026-07-24
Verified against Git: branch `codex/v2-financial-close-core`, commit `9cc4c91a45a56476428b2e7cddacccea9e0f355d`, clean worktree before this documentation update

## Executive state

BRAVO retains its existing platform shell (identity, application RLS, retrieval, tools, draft
approval, audit, checkpoints and deployment). The current direction remains a **framework-
independent Conversation Core V2** behind that shell, beginning with the Financial Close Advisor.
It is not approval to keep broad-patching the legacy agent loop, nor to rewrite the entire
platform.

The project has completed and tested a code-level P0 containment increment since the previous
snapshot. It has **not** yet frozen a real A/B answer baseline, built the clean Core V2 domain
package, run the 24-trajectory blind evaluation, or passed the production/platform gates. The
Engineering Workbench and frontend prototype tracks remain independent and are not evidence that
conversation quality has improved.

## Verified baseline

| Item | Verified state | Evidence / limit |
|---|---|---|
| Git baseline | Clean at `9cc4c91` before this documentation pass | Current branch is `codex/v2-financial-close-core`; this pass changes documentation only |
| Alembic | `0017_native_rls_backstop` is the single head | `python -m alembic heads` |
| Python test suite | 404 passed, 41 skipped | `python -m pytest -q -p no:cacheprovider`, 2026-07-24; skipped tests are not a DB/production pass |
| Focused containment/evaluation tests | 17 passed, 5 skipped | Owner authorization, answer-guard parity, CAS state, native-RLS, replay/C0/SME/release-gate contracts |
| Markdown documentation | 254 tracked Markdown files, 0 broken relative-link occurrences | `docs/documentation/MARKDOWN-INVENTORY.md`; two intentional import duplicates remain review signals |
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
| Conversation Core V2 / Financial Close Advisor | Not started as a clean domain package | The existing Consultant workflow cards and frontend Financial Close prototype are not Core V2 |
| BravoGen R0 collection | Complete as black-box behavioral evidence | BravoGen internals or BRAVO knowledge truth |

## Gates still open

No production, security, or quality claim may be made until the following evidence exists:

1. Rotate the previously exposed provider credential; verify effective production Compose exposes
   only approved ingress, uses non-default database/Keycloak credentials, and authenticates Redis.
2. Provision separate non-owner runtime roles, arm native RLS deliberately, and pass negative
   HTTP, MCP and worker probes with a real PostgreSQL environment. Extend native policy coverage
   beyond `chunks` before relying on it as a database backstop.
3. Run clean `0012 -> head` migration, downgrade/upgrade and all security-critical DB integration
   checks without skips; perform an isolated backup/restore drill including private operational
   data.
4. Freeze System A and B answers, traces, model/version, prompts and `EvidenceBundle` before
   changing routing, retrieval, prompts or synthesis. The repository currently contains tooling,
   not a frozen answer artifact.
5. Author and validate the Financial Close evidence pack and benchmark contracts; obtain the
   required reviewer calibration and blind SME evidence before judging Core V2.
6. Independently run frontend typecheck/test/build and the controlled offline/egress smoke before
   making frontend or on-prem readiness claims.

## Next authorized implementation sequence

1. Use the current clean commit as the named code baseline and record the redacted environment,
   lockfile hashes and effective Compose evidence in a controlled run artifact.
2. Complete the operational containment proofs above. If the required runtime roles, maintenance
   window, credentials or backup target are unavailable, record the gate as blocked rather than
   simulating a pass.
3. Freeze the matched System A/B Financial Close anchors with no further prompt, routing,
   retrieval or synthesis edits.
4. Only then create the framework-independent Core V2 contracts and the single Financial Close
   vertical slice behind narrow ports.

## Source of truth and precedence

1. Reproducible code, tests, migrations and runtime evidence override prose claims.
2. This file owns the current snapshot; `docs/AI-REVIEW-MANIFEST.md` owns the bounded review set.
3. Accepted ADRs own existing platform invariants; the `plan-rebuild/04–08` documents own the V2
   decision design and gates.
4. `docs/research/**`, `docs/reviews/**`, `docs/work-packages/**`, `plan-rebuild/bravogen-p0/**`,
   `file_system/**` Markdown, and archive directories are retained evidence/reference only. Do
   not treat them as current progress without fresh verification.