# WP19-00 containment and baseline record

Captured before the WP19 legacy router containment edit.

- Worktree: clean before the change; baseline commit
  `628eecf71f964b85fac37fa838e7918aa3f618cd`.
- Source migration head: `0020_case_v2_audit`, recorded in
  [runtime-baseline.json](runtime-baseline.json). The live database `alembic current` probe is
  **blocked**: the configured database host could not be resolved. This is not treated as a pass.
- The generated manifest reads no `.env`, records no environment values or credentials, and uses a
  static (non-interpolated) Compose projection only.
- Active feature flags and model/version identifiers are **not collected** because determining them
  would require a live controlled runtime or reading a secret/configuration store. No arm is marked
  enabled on the basis of defaults or historical evidence.
- System A/B capture for the ten-transaction anchor is **blocked**: no controlled running API,
  database, evidence snapshot, or proven active Consultant configuration is available in this
  workspace. The existing historical A/B artifact is not reused as proof because Plan 19 identified
  it as insufficient to prove System B behavior.

The next operator-run capture must use a clean, isolated environment, a pinned model/version,
matched evidence snapshots, and the existing immutable frozen-baseline writer. It must not record
credentials or raw secret configuration.

## Isolated environment attempt — 2026-08-18

The owner authorized an isolated `bravo-wp19` Compose environment. A new ignored `.env.wp00` was
generated without printing its values. Docker Desktop was reachable, but the image build stopped
before any service container was created because Docker could not validate the Docker Hub TLS
certificate for `python:3.11-slim` and `node:20-slim` (`x509: certificate signed by unknown
authority`). No certificate verification was bypassed, and no runtime, migration or A/B result is
claimed. Restore the trusted Docker CA/proxy configuration or provide pre-verified base images,
then rerun the isolated environment procedure.

## Continuation preflight — 2026-08-18

Docker Desktop connectivity was subsequently restored without disabling certificate verification.
The following source images were pulled successfully: `python:3.11-slim`, `node:20-slim`,
`pgvector/pgvector:pg16`, and `redis:7-alpine`.

The first Compose invocation auto-loaded `docker-compose.override.yml` and could not bind local
port 6379 because it was already in use. Re-running with the base `docker-compose.yml` only
created the isolated `bravo-wp19` network and volume without publishing PostgreSQL or Redis to the
host. PostgreSQL reached its Compose healthcheck and Redis accepted connections. `alembic upgrade
head` completed against this new synthetic database through head `0020_case_v2_audit`.

The full current Docker image build remains blocked by dependency-network behavior outside the
application: npm 10.8.2 in `node:20-slim` reports `Exit handler never called` and leaves the
frontend build without `tsc`; a clean rebuild also receives HTTP 403 for Debian APT repositories.
The Dockerfile now uses the lockfile-respecting `npm ci` command, but this does not bypass either
network control and has not produced a complete image.

To validate the API/database prerequisite without treating it as a reproducible release image, an
existing Python dependency image (`bravo-migration-check-test@sha256:756a0acc36e404d11c92c9a3bd77c66fe658cd91fbf9089e17d269d87bd45860`)
ran the current workspace source through a read-only mount. Its API-only harness started successfully
and returned `200` from `/health` on host-bound `127.0.0.1:18000`. This harness is preflight evidence
only; it is not a frozen A/B runtime image and it does not authorize a quality claim.

No chat/model request was made. There is still no owner-approved, immutable model/configuration
record for this run, so the synthetic A/B capture remains **BLOCKED** under the external-gate
packet. Fixture and baseline tooling checks passed: `6 passed` (`test_conversation_v2_wp19_fixture.py`
and `test_frozen_ab_baseline.py`). No environment value, DSN, password, token, or API key was read
into this record.

## Network remediation and reproducible image — 2026-08-18

After the owner selected the approved proxy/allowlist remediation, in-container probes returned
HTTP `200` for `https://registry.npmjs.org/-/ping`,
`https://registry.npmjs.org/typescript`, and both HTTP and HTTPS Debian `InRelease` endpoints.
TLS verification remained enabled throughout.

A fresh `--no-cache` API build then completed successfully: npm installed 568 locked packages,
the frontend production build completed, and the API image resolved to
`sha256:68c79d747417a88b153bfe866d5c26938fc2bc95482f345b6a8910bba1891b36`.
The temporary mounted-source harness was replaced by this image. The image-backed API returned
`200` from `/health` on `127.0.0.1:18000`; PostgreSQL remained healthy and Redis remained running
inside the isolated project network.

Focused regression after the image build: `14 passed` (`test_bravo_intent.py`,
`test_conversation_v2_wp19_fixture.py`, and `test_frozen_ab_baseline.py`). The API/database
environment and reproducible-image prerequisites are therefore ready. The frozen A/B capture is
still intentionally not run: the worktree must first be cleaned/frozen and an owner-approved,
immutable model/configuration record must be bound to the run. No chat/model request or secret
value was recorded during this remediation.

## Model configuration record — 2026-08-18

The owner selected the synthetic-only cloud runtime below. This is the sole short model record;
it contains no credential or secret-store value.

| Field | Value |
|---|---|
| Provider | OpenAI API |
| Deployment policy | `cloud_only`, synthetic A/B only |
| API base URL | `https://api.openai.com/v1` |
| Requested alias | `gpt-4o` |
| Pinned model revision | `gpt-4o-2024-11-20` |
| Runtime image | `bravo-wp19-api@sha256:68c79d747417a88b153bfe866d5c26938fc2bc95482f345b6a8910bba1891b36` |

The non-secret cloud policy/base URL/model settings were applied to the ignored `.env.wp00` file.
The configuration helper intentionally refused activation because `CLOUD_API_KEY` is absent. A
non-network offline check against a synthetic temporary configuration confirmed that it preserves
the approved snapshot and enables the required cloud flags. The final activation, API restart and
non-prompt authenticated endpoint preflight remain pending secret-manager injection of the API key.
No model completion or A/B capture has been run.
