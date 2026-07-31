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
