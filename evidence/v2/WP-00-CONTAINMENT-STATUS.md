# WP-00 containment and baseline status

Status: `BLOCKED — runtime and immutable answer-baseline evidence is not available`

Recorded: 2026-07-31 (UTC)

## Static evidence captured

- Named source baseline: `24209ab10535aba2f6facc0cc1bdc766e7eac079`
- Branch at capture: `codex/v2-financial-close-core`
- Alembic source head: `0017_native_rls_backstop`
- Redaction-safe manifest: [`wp-00-runtime-baseline.json`](wp-00-runtime-baseline.json)
- Static production Compose projection: only Caddy publishes `80:80` and `443:443`; no Keycloak service is declared.
- The manifest neither reads `.env` nor records environment values or credentials.

## Checks completed locally

- Focused containment contracts: `25 passed, 9 skipped`.
- Frontend typecheck: passed.
- Frontend tests: `3 files, 7 tests passed` using a single forked Vitest worker. The default worker pool did not terminate within 60 seconds and is not used as evidence.
- Frontend production build: passed.

## Blocking conditions

1. The worktree is not clean: it contains user-owned plan/ADR/documentation changes. They were not altered or discarded, so this capture cannot be a clean-worktree baseline.
2. Docker Desktop is not running. Therefore no live PostgreSQL environment is available for clean migration/downgrade/upgrade, native-RLS cutover, HTTP/MCP/worker isolation probes, or an isolated backup/restore drill.
3. Provider-credential rotation and non-owner runtime-role provisioning require the responsible operator and secret/runtime access. No secret store or `.env` file was inspected.
4. No frozen synthetic A/B answer and trace artifacts, pinned model/version record, or SME-reviewed answer key was supplied. The replay utility exists, but running it requires an intentionally started local service and synthetic evaluation credentials.

## Gate decision

WP-00 is **not passed**. Per the accepted dependency order, WP-01 through WP-10 remain closed: no prompt, routing, retrieval, synthesis, case-core, deterministic-engine, API, or UI implementation was started from this run.

## 2026-07-31 remediation update

- The documentation/evidence baseline was committed as `6fe51f32217babfcaeeedef51a283a453728afae`; the worktree was clean before the remediation tooling in this update.
- Docker Desktop is reachable, but the only discovered Compose container (`postgres`) is stopped. No API, worker, or Redis runtime proof exists.
- Production Compose correctly rejects a missing `REDIS_PASSWORD`. This remains a blocked secret-injection gate, not a configuration pass.
- `deploy/runtime-roles.sql` and `deploy/docker-compose.rls-cutover.yml` now provide an explicit non-owner API/MCP versus worker cutover path. They contain no password and must be executed by the responsible database/secrets operator.
- `app.eval.frozen_ab_baseline` now refuses incomplete A/B captures and binds each new synthetic baseline to fixture, replay, evidence, model/version, and prompt hashes without recording credentials.

## 2026-07-31 development-configuration update (current status)

This section supersedes the older workstation observations above where they conflict.

- Current committed head observed before this update: `4ceabc4c79c3aa5e9864d24d447304e1ec5e541e`.
- The current worktree contains uncommitted containment/configuration changes. It must be reviewed
  and committed before recording the next clean code baseline or reopening any package.
- The sole retained, gitignored deployment file is `.env.wp00`; no secret value is recorded in
  this artifact. It selects cloud LLM and `openai_compatible` cloud embedding model
  `text-embedding-3-small` with `EMBEDDING_DIM=1536`. Local LLM and reranking are explicitly
  disabled. Dedicated embedding credentials remain optional because the adapter safely falls back
  to the already approved cloud LLM endpoint/key without duplicating them in the environment file.
- Production Compose plus the explicit RLS-cutover overlay validates without rendering secrets.
  No `bravo-wp00` volume exists, so the first isolated migration can create a clean 1536-dimension
  Vector schema; an old 1024-dimension database must not be reused.
- Focused development checks: `9 passed` for cloud embedding, baseline freezing, and native-RLS
  cutover preflight contracts.

### Continuation decision

Configuration preparation is complete, but **WP-00 remains blocked**. Before WP-01 may start, the
operator must: commit the current changes; start the isolated `bravo-wp00` stack; run clean
`0012 -> head` migration and downgrade/upgrade evidence; provision non-owner roles; arm and probe
native RLS through HTTP/MCP/worker; complete isolated backup/restore; and freeze the synthetic A/B
answer/trace artifact. Do not create Bank fixtures, Core V2, prompts, routing, retrieval, APIs, or
case UI until those runtime and baseline records exist.
