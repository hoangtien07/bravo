# T6 — Egress, Secrets, Deployment & Operations

Scope read: T0–T2 artifacts; `.env.example`, `Dockerfile`, compose/deploy/backup/CI files, `.gitignore`, `app/config.py`, LLM/embedding/rerank/observability/worker code, and direct policy validation modules. No deployed `.env`, database, network policy, or container runtime was read. No test was run because the host Python toolchain is unavailable.

## Environment → consumer → validation matrix

| Setting group | Primary consumer | Default / compose value | Validation observed |
|---|---|---|---|
| `ENV`, `LOG_LEVEL` | `app.main`, `Settings` | `local`, `INFO`; prod overlay sets `ENV=production` | `ENV` gates production secret/OIDC checks; log level is parsed only |
| `DATABASE_URL` | `app.database`, Alembic, backup | Local `bravo:bravo`; CI uses same value | No boot connectivity, migration-head, credential-strength, or role/grant validation |
| `JWT_SECRET`, `MCP_TOKEN_PEPPER` | JWT/token hashing | Placeholder defaults | Production boot rejects configured weak/short values |
| Local LLM endpoint/model/key | `app.llm.router` | `localhost:8001`, Qwen default, `dummy` key | Client timeout/retries; no endpoint preflight |
| Cloud chat settings | `app.llm.router` | Disabled/empty | Boot rejects cloud enabled without cloud key/base URL; router uses sensitivity/task gates |
| Cloud embedding settings | `app.rag.embedding` | Empty; provider defaults local | Per-call `sensitive=True` blocks cloud; configuration completeness/dimension compatibility not boot-validated |
| Rerank settings | `app.rag.retriever`, `rag.rerank` | Disabled; provider `viranker` | No validation of `rerank_provider` or sensitivity propagation |
| Path roots/policy | Config data-policy loader; compose mounts | `/app/file_system`, `/app/data/uploads`, `/app/data/private` in compose | Shared/rule paths audited; paths marked `ensure_exists` are created at boot |
| `REDIS_URL` | `app.worker`/arq | `redis://localhost:6379/0` | No connection preflight found |
| OIDC/session settings | OIDC routes/session middleware | Disabled/empty | Production conditional validation for session secret and OIDC fields |
| CORS/rate limit | `app.main`, `app.ratelimit` | Empty origins; `30`/minute | CORS added only with configured origins; rate middleware enabled when value >0, but decorator coverage is route-specific |
| Metrics/OTel | `app.observability` | Metrics enabled; OTLP empty | Metrics route is installed when enabled; OTLP endpoint is accepted without reachability/auth validation |

## Deployment and data-path evidence

| Boundary | Implementation evidence | Assessment |
|---|---|---|
| Shared corpus | API and worker compose services mount `./file_system:/app/file_system:ro`; Docker image does not copy this directory. | Compose is the provisioning layer; policy validation is not a mount/permission control. |
| Upload/private runtime data | Both services mount named `uploads` and `private_data` volumes to the configured paths. | Paths are provisioned in compose; T6 findings cover lifecycle/backup/config drift. |
| Inbound public surface | Prod overlay adds Caddy on host ports 80/443; its only path rule blocks API docs and otherwise proxies to `api:8000`. | The provided Caddy configuration does not block `/readyz` or `/metrics`. Actual external firewall/DNS policy is `NEED FILE/CONTEXT`. |
| Container privilege | Dockerfile has no `USER`; compose files have no `user`, `read_only`, capability-drop, or security-opt directives. | API/worker run with the image default user and writable root filesystem in the supplied configuration. |
| Secrets in tracked files | `.env` is ignored; tracked-secret pattern scan found only template/placeholders and CI/dev PostgreSQL values. | No real credential is established by this scan; untracked/deployed secrets and Git history were not read. |
| Backup | `scripts/backup.sh` dumps DB and backs up `uploads` only; compose also provisions `private_data`. | Private volume and a runnable restore procedure are not covered by the executable backup scope. |

## Egress trace

| Path | Guard/audit evidence | Status |
|---|---|---|
| Chat and streaming chat | `llm.router.decide` selects cloud only with enabled cloud config, non-sensitive context, and allowed task; cloud route calls `_audit_egress` before request. | VERIFIED static control; actual runtime settings are `NEED FILE/CONTEXT`. |
| Cloud embeddings | `embedding.embed` raises for `sensitive=True` before calling provider and logs only a content hash. | VERIFIED static control; caller classification is T3 scope. |
| LLM rerank | `retriever.retrieve` forwards retrieved passage content to `llm_rerank`; `llm_rerank` sets `sensitive=False` and allows cloud. | See BRV-PLAT-001. |
| Observability | LLM egress audit stores provider/model/prompt hash; metrics count backend/token/tool labels. | Code does not persist raw prompt in `AuditLog`; network/auth for OTLP/metrics is deployment context. |

## Findings

| ID | Severity tạm thời | Evidence state | File:symbol | Evidence ngắn | Consumer/impact | Next action | Needs Sol review |
|---|---|---|---|---|---|---|---|
| BRV-API-003 | Medium | VERIFIED | `app/main.py` rate-limit setup; `docker-compose*.yml` | Compose provides `RATE_LIMIT_PER_MINUTE` through `.env`, but no deployment layer adds limits to `/api/ask`, `/api/agent/ask`, or scan routes; only the chat-stream decorator exists (T1). | T1 gap remains active in supplied deployment configuration. | Retain T1 ID; add route-level coverage after defining endpoint limits. | No |
| BRV-API-004 | Medium | VERIFIED | `deploy/Caddyfile`; `app/main.py:readyz` | Caddy only matches docs paths before `reverse_proxy api:8000`; `/readyz` is forwarded and returns raw DB exception text on failure (T1). | The supplied public reverse-proxy path does not mitigate readiness error disclosure. | Retain T1 ID; block or sanitize readiness externally and verify deployed network policy. | No |
| BRV-API-005 | Low | VERIFIED | `deploy/Caddyfile`; `app/observability.py:setup` | Metrics are exposed at `/metrics` when enabled and Caddy proxies unmatched paths, including `/metrics`. | The supplied proxy configuration does not restrict metrics; actual firewall/access policy is unknown. | Retain T1 ID; choose network or application protection and test it. | No |
| BRV-API-006 | Low | VERIFIED | `deploy/Caddyfile:reverse_proxy`; T1 raw-error paths | Caddy has no response transformation/error-redaction rule; upstream error bodies are proxied by the configured default route. | Deployment does not mitigate the authenticated raw-exception exposure found in T1. | Retain T1 ID; replace client error detail at the application boundary. | No |
| BRV-PLAT-001 | High (conditional) | VERIFIED | `app/rag/retriever.py:retrieve`; `app/rag/rerank.py:llm_rerank` | When rerank is enabled with provider `llm`, retrieved passage text is embedded in the prompt while `llm.chat` is called with explicit `sensitive=False` and `allow_cloud_task=True`; this bypasses router context classification. | If cloud chat and LLM rerank are enabled, department-scoped/private passages can be sent to cloud. Defaults disable rerank, but the configuration permits this failure path. | Sol must decide egress policy for reranking; T3 verify source classifications and add a sensitive-rerank regression test. | Yes |
| BRV-PLAT-002 | Medium | VERIFIED | `docker-compose.yml:postgres`; `docker-compose.prod.yml` | Base compose hard-codes `POSTGRES_PASSWORD: bravo`; production overlay retains that service configuration, and `.env.example` provides matching API credentials. `validate_boot` does not validate database credential strength. | The supplied production compose path can run with a known database password on the internal network. | Parameterize/provision DB credentials separately and add a production preflight that rejects the known default. | No |
| BRV-PLAT-003 | Medium | VERIFIED | `docker-compose*.yml` volume declarations; `scripts/backup.sh` | API/worker mount `private_data`, but backup handles database plus `uploads`/`bravo_uploads` only. No restore executable was found under `scripts/` or `deploy/`. | Private operational data has no corresponding backup artifact; recovery behavior cannot be verified from executable code. | Include private-data backup and an executable/validated restore path; T2 retention and T3 corpus decisions remain separate. | No |
| BRV-PLAT-004 | Medium | VERIFIED | `app/config.py:data_policy_variables`; `app/api/routes_sources.py:_DATA_DIR` | Settings expose `UPLOAD_ROOT`, but source upload/read code uses fixed relative `Path("data/uploads")` instead of the configured value. | A non-default upload-root deployment can pass policy validation while source files are written/read from a different path. | Route consumers should use the resolved runtime path; add a non-default-path integration test. | No |
| BRV-PLAT-005 | Medium | VERIFIED | `app/config.py:validate_data_runtime_policy`; `app/eval/bravo_data_policy.py:ensure_runtime_policy_paths` | Boot creates `UPLOAD_ROOT` and `PRIVATE_DATA_ROOT` for rules marked `ensure_exists` before audit; it does not distinguish a provisioned volume from a newly created container directory. | A missing mutable-data mount can be masked by an empty writable directory, risking ephemeral or misplaced runtime data. | Make volume/provisioning verification explicit in production preflight; do not treat policy directory creation as mount evidence. | No |
| BRV-PLAT-006 | Medium | VERIFIED | `app/main.py:lifespan`; `app/config.py:validate_boot`; `alembic/env.py` | Startup validates policy/config and loads catalog but does not test DB connectivity, Alembic head, or existing vector dimension. Migration is invoked by CI/bootstrap only. | A plain production compose start can serve a process that later fails readiness or vector operations because DB/schema/dimension state is not startup-gated. | Add a deployment preflight/readiness gate for DB, migration head, and embedding dimension; T3 verifies embedding use. | No |
| BRV-PLAT-007 | Medium | VERIFIED | `deploy/docker-compose.keycloak.yml:keycloak` | Optional Keycloak overlay binds port 8080 and sets bootstrap admin username/password to `admin`/`admin` while running `start-dev`. | Enabling this overlay as supplied exposes a predictable IdP administrator credential. | Require externally provisioned bootstrap secrets and a production Keycloak mode before use. | No |
| BRV-PLAT-008 | Low | VERIFIED | `Dockerfile`; `docker-compose*.yml` | The production API/worker image has no non-root `USER` and compose adds no filesystem/capability restrictions; both services receive writable runtime volumes. | A compromised process has the container default-user permissions across its writable filesystem and mounted mutable volumes. | Define least-privilege container user/filesystem controls and verify required upload/worker writes. | No |

## Test evidence and operational gaps

| Evidence | State | Notes |
|---|---|---|
| `tests/test_router_egress.py` checks local selection for sensitive context and audit-record creation. | Read only; not executed | Does not exercise LLM rerank or deployment settings. |
| `tests/test_egress_embedding.py` checks per-call sensitive cloud-embedding refusal and hash logging. | Read only; not executed | Does not prove caller-supplied sensitivity is correct. |
| `tests/test_wave2.py` checks selected production boot guards. | Read only; not executed | No test for database defaults, mount presence, DB/migration/vector preflight, backup/restore, or proxy path exposure. |
| Expected scoped command | `pytest -q tests/test_router_egress.py tests/test_egress_embedding.py tests/test_wave2.py` | Not run: host Python/pytest unavailable. |

## Policy versus provisioning boundary

`bravo_data_runtime_policy` is loaded and audited by application code. It classifies paths and may create explicitly marked runtime directories; it does not establish Docker mounts, filesystem ownership, Caddy access controls, database roles, firewall rules, external secret stores, or backup schedules. Those require deployment evidence not present in the repository.

## T6 exit check

- T1 deployment findings BRV-API-003 through BRV-API-006 are followed up with concrete configuration/proxy evidence.
- Egress routes, tracked-secret handling, path mounts, boot checks, and backup scope are mapped without treating external network assumptions as implementation evidence.
- Policy and provisioning controls are separated. No production code, configuration, migration, or test was changed.
