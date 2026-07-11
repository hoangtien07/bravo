# T0 — Inventory, Dependency & Test Baseline

Collected from repository metadata, file names, imports/references, configuration definitions, CI/deployment files, and read-only command output on 2026-07-10. This artifact contains no architecture, security, business, or severity findings.

## Repository metadata

| Item | Observed evidence |
|---|---|
| Repository root | `D:/VsCode/Workspace/bravo` (`git rev-parse --show-toplevel`) |
| Current branch | `bravo-v0.1` |
| Current commit | `5b571428264bb2bca5bb590840f8436f1ffe1643` |
| Working tree | `git status --short` reported modified: `.env.example`, `.gitignore`, `app/config.py`, `app/eval/bravo_readiness.py`, `docker-compose.prod.yml`, `docker-compose.yml`, `docs/DEPLOY-GCP.md`, `docs/RUNBOOK-PACKAGING.md`, `scripts/ingest_userguide.py`; untracked: `app/eval/bravo_data_audit.py`, `app/eval/bravo_data_policy.py`, `docs/BRAVO-DATA-RUNTIME-CLASSIFICATION.md`, `file_system/bravo_data_runtime_policy.yaml`, `tests/test_bravo_data_audit.py` |
| Python | `pyproject.toml` requires `>=3.11`; `Dockerfile` uses Python 3.11; CI uses Python 3.12. Host `python`/`py` commands were not found. |
| Node/package manager | Docker frontend stage uses Node 20 and npm; host `node --version` returned `v24.16.0`; host `npm` command was not found. `frontend-react/package-lock.json` exists. |
| Backend entrypoint | `app/main.py`, object `app`; Docker command `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Frontend entrypoint | `frontend-react/src/main.tsx`; Vite config `frontend-react/vite.config.ts`; built SPA is served by `app.main` from `frontend-react/dist` when present |
| Worker/background entrypoint | `app/worker.py`, `WorkerSettings`; compose command `arq app.worker.WorkerSettings` |
| Migration framework | Alembic (`alembic.ini`, `alembic/env.py`, `alembic/versions/0001`–`0007`) |
| Test framework | pytest and pytest-asyncio in `[project.optional-dependencies].dev`; `asyncio_mode = "auto"` in `pyproject.toml` |
| Lint/type tools | Ruff and mypy are dev dependencies; CI executes `ruff check app`; no separate type-check CI step was observed |
| Docker/deployment entrypoints | `Dockerfile`; `docker-compose.yml`; `docker-compose.prod.yml`; `deploy/bootstrap.sh`; `deploy/Caddyfile`; optional compose overlays for Keycloak and observability |

## Entrypoints

| Runtime | Path/symbol or command | Evidence |
|---|---|---|
| HTTP API | `app/main.py:app` | FastAPI application object; Docker/compose Uvicorn command |
| API routes | `app/api/routes_*.py` | Route modules are imported/mounted by `app/main.py` |
| Frontend | `frontend-react/src/main.tsx` → `frontend-react/src/App.tsx` | Vite package and source entry files |
| Background work | `app/worker.py:WorkerSettings` | Compose `arq app.worker.WorkerSettings` |
| Database migration | `alembic upgrade head` | `.github/workflows/ci.yml`, `deploy/bootstrap.sh`, README/DEV docs |
| Evaluation | `python -m app.eval.run --passk --mock --k=8` | `.github/workflows/ci.yml` |

## Directory inventory

Maximum displayed depth is five levels; generated/dependency/cache directories are omitted.

```text
.
├── .agents/
├── .claude/{agents,skills/{adr-new,council-review,rag-ingest-design,rls-check}}/
├── .github/workflows/ci.yml
├── alembic/{env.py,versions/}
├── app/
│   ├── accounting/{data}/
│   ├── agent/
│   ├── api/
│   ├── database/
│   ├── data_layer/
│   ├── erp/
│   ├── eval/
│   ├── ingestion/
│   ├── llm/
│   ├── mcp/
│   ├── rag/
│   ├── security/
│   └── utils/
├── data/{private/,uploads/}
├── deploy/{Caddyfile,bootstrap.sh,docker-compose.keycloak.yml,docker-compose.observability.yml,site.yaml.example}
├── docs/{adr/,reference/,research/{findings/},work-packages/}
├── file_system/{Data/,KQPT_PTNV/,Mindmaps/,TaiLieuKyThuat_Dll/,UserGuide_B10_TV_PDF/,*.yaml,*.pdf,*.docx}
├── frontend-react/{src/{api,components,features,lib,store},package.json,package-lock.json,vite.config.ts,tsconfig.json}
├── scripts/{seed*.py,ingest_userguide.py,build_coa_from_xlsx.py,backup.sh}
├── tests/{eval/,fixtures/{invoices,invoices_demo},test_*.py}
├── scratch_multipart/
├── scratch_test/pyproject.toml
└── {Dockerfile,alembic.ini,docker-compose.yml,docker-compose.prod.yml,.env.example,pyproject.toml,uv.lock}
```

## Module and consumer map

| Module/domain | Primary paths | Entrypoint/consumer | Tests | Notes |
|---|---|---|---|---|
| API/routes | `app/main.py`, `app/api/` | FastAPI app; route modules mounted by `app/main.py` | `tests/test_http_health.py`, `test_chat.py`, `test_admin.py`, route-specific tests | Route file inventory only |
| Security/auth | `app/security/auth.py`, `passwords.py`, `sensitivity.py`, `ratelimit.py` | API dependencies and LLM/egress classification consumers | `test_rls.py`, `test_sensitivity.py`, `test_wave2.py`, `test_admin.py` | JWT/OIDC/MCP token paths are represented in source files |
| Database/RLS | `app/database/`, `app/security/rls.py`, `alembic/` | API dependencies, agent/memory and migrations | `test_data_layer.py`, `test_rls.py`, `test_memory_rls.py`, DB-backed admin/agent tests | PostgreSQL/pgvector named in compose and dependencies |
| Agent | `app/agent/loop.py`, `context.py`, `runs.py`, `conversations.py` | `routes_agent.py`, `routes_agents.py`, chat routes | `test_agent_loop.py`, `test_agent_runs.py`, `test_chat.py`, `test_streaming_wave1.py` | Agent files are mapped, not reviewed |
| Memory | `app/agent/memory.py` | Agent context/recall and database models | `test_memory_rls.py` | Consumer paths identified by imports/references |
| RAG | `app/rag/{retriever,rerank,embedding,bravo_intent}.py` | Agent `kb_search` path; ingestion-produced chunks | `test_grounding.py`, `test_egress_embedding.py`, `test_bravo_intent.py` | Retrieval/embedding symbols only |
| Ingestion | `app/ingestion/`, `scripts/ingest_userguide.py` | Ingestion pipeline and worker | `test_ingestion_wpa.py`, `test_bravo_corpus_manifest.py`, `test_invoice_parser.py` | Manifest at `file_system/bravo_corpus_manifest.yaml` |
| Accounting/tax | `app/accounting/`, `app/agent/tax.py`, `app/agent/anomaly.py` | API invoice/money/anomaly routes and agent tools | `test_accounting_rules.py`, `test_ap_*.py`, `test_coa.py`, `test_journal*.py`, `test_tax.py`, `test_anomaly.py` | Rule data under `app/accounting/data/` |
| ERP integration | `app/erp/{client,draft_queue}.py`, `app/api/routes_drafts.py` | Draft queue/API consumers | `test_draft_queue.py`, `test_draft_leak_probe.py`, `test_agent_runs.py` | No separate ERP service source tree observed |
| MCP/tools | `app/mcp/server.py`, `app/agent/tools.py` | `/mcp` mount in `app/main.py`; agent registry/executor | `test_mcp_server.py`, `test_agent_loop.py` | Tool registry path is `app/agent/tools.py` |
| LLM routing | `app/llm/router.py` | Agent loop and embedding/rerank providers | `test_router_egress.py`, `test_sensitivity.py`, `test_streaming_wave1.py` | Provider config in `app/config.py` |
| Evaluation | `app/eval/`, `tests/eval/`, `tests/test_*readiness*`, `test_eval_passk.py` | CI pass-k command and readiness modules | `tests/eval/*`, `test_eval_passk.py`, `test_bravo_*` | Golden/policy/playbook paths listed below |
| Observability | `app/observability.py` | `app/main.py` instrumentation; Prometheus/OTel deps | `test_wave2.py` | Metrics/OTLP config fields in `app/config.py` |
| Worker/background jobs | `app/worker.py` | Compose `worker` service and Redis | No dedicated worker command test identified; `test_ingestion_wpa.py` covers ingestion helpers | `arq`/`redis` dependencies |
| Frontend | `frontend-react/src/`, `frontend-react/src/api/` | Vite scripts; API client/types/SSE modules | No frontend test runner/script observed | `npm run build` performs TypeScript no-emit then Vite build |
| Deployment | `Dockerfile`, compose files, `deploy/` | Docker build, compose services, bootstrap script | CI/deployment commands; no deployment test suite identified | Postgres, Redis, API, worker, optional Caddy/Keycloak/observability |

## Environment/config map

Definitions/defaults come from `app/config.py`, `.env.example`, and compose overrides. “Required/optional evidence” records only whether a default or explicit requirement is visible; it does not assess safety.

| Variable | Defined/documented at | Consumers | Default | Required/optional evidence | Validation location |
|---|---|---|---|---|---|
| `APP_ROOT` | `app/config.py:26`, `.env.example`, compose | `Settings.data_policy_variables`, data-policy audit | empty; resolves current working directory | optional default observed | `app/config.py:validate_data_runtime_policy` |
| `DATA_ROOT` | `app/config.py:27`, `.env.example`, compose | data policy; derived upload/private paths | empty; derives under app root | optional default observed | `app/eval/bravo_data_policy.py` |
| `CORPUS_ROOT` | `app/config.py:28`, `.env.example`, compose | RAG/ingestion/eval manifest consumers | empty; resolves `file_system` | optional default observed | data-policy validation |
| `UPLOAD_ROOT` | `app/config.py:29`, `.env.example`, compose | `app/api/routes_sources.py`, data policy | empty; derives `DATA_ROOT/uploads` | optional default observed | data-policy validation |
| `PRIVATE_DATA_ROOT` | `app/config.py:30`, `.env.example`, compose | data policy/audit and runtime path consumers | empty; derives `DATA_ROOT/private` | optional default observed | data-policy validation |
| `DATA_RUNTIME_POLICY` | `app/config.py:31-34`, `.env.example`, compose | boot data-policy loader/audit | `file_system/bravo_data_runtime_policy.yaml` | default observed | `Settings.validate_data_runtime_policy` |
| `EMBEDDING_DIM` | `app/config.py:63`, `.env.example` | `app/rag/embedding.py`, vector schema usage | `1024` | optional default observed | `Settings` parsing; schema consumers |
| `EMBEDDING_PROVIDER` | `app/config.py:61`, `.env.example` | `app/rag/embedding.py`, LLM provider selection | `local` | optional default observed | provider selection in RAG code |
| `EMBEDDING_MODEL` | `app/config.py:62`, `.env.example` | `app/rag/embedding.py` | `BAAI/bge-m3` | optional default observed | provider selection |
| `CLOUD_EMBEDDING_BASE_URL` | `app/config.py:65`, `.env.example` | cloud-compatible embedding branch | empty | optional field observed | provider code; no separate validator located |
| `CLOUD_EMBEDDING_MODEL` | `app/config.py:66`, `.env.example` | cloud-compatible embedding branch | empty | optional field observed | provider code; no separate validator located |
| `CLOUD_EMBEDDING_API_KEY` | `app/config.py:67`, `.env.example` | cloud-compatible embedding branch | empty | optional field observed | provider code; no separate validator located |
| `DATABASE_URL` | `app/config.py:37`, `.env.example`, CI | `app/database/__init__.py`, Alembic, tests | local PostgreSQL URL | default observed; CI explicitly sets | SQLAlchemy/Alembic initialization |
| `LLM_LOCAL_BASE_URL` | `app/config.py:48`, `.env.example` | `app/llm/router.py` | `http://localhost:8001/v1` | optional default observed | router construction |
| `LLM_LOCAL_MODEL` | `app/config.py:49`, `.env.example` | `app/llm/router.py` | `Qwen2.5-32B-Instruct-AWQ` | optional default observed | router construction |
| `LLM_LOCAL_API_KEY` | `app/config.py:50`, `.env.example` | `app/llm/router.py` | `dummy` | optional default observed | router construction |
| `CLOUD_ENABLED` | `app/config.py:53`, `.env.example` | router and boot validation | `false` | optional default observed | `Settings.validate_data_runtime_policy` |
| `CLOUD_BASE_URL` | `app/config.py:54`, `.env.example` | cloud LLM router | empty | conditional field observed | boot check when cloud enabled |
| `CLOUD_MODEL` | `app/config.py:55`, `.env.example` | cloud LLM router | empty | conditional field observed | router/boot context |
| `CLOUD_API_KEY` | `app/config.py:56`, `.env.example` | cloud LLM router | empty | conditional field observed | boot check when cloud enabled |
| `REDIS_URL` | `app/config.py:90`, `.env.example`, compose | `app/worker.py`/arq and queue consumers | `redis://localhost:6379/0` | optional default observed | worker initialization |
| `LOG_LEVEL` | `app/config.py:17`, `.env.example` | application logging setup | `INFO` | optional default observed | logging setup; no separate validator located |
| `METRICS_ENABLED` | `app/config.py:96`, `.env.example` | `app/observability.py` | `true` | optional default observed | observability setup |
| `OTEL_EXPORTER_ENDPOINT` | `app/config.py:97`, `.env.example`, optional compose | `app/observability.py` | empty | optional field observed | observability setup |
| `RATE_LIMIT_PER_MINUTE` | `app/config.py:100`, `.env.example` | `app/ratelimit.py`/API | `30` | optional default observed | rate-limit setup |
| `LLM_MAX_CONCURRENCY` | `app/config.py:101`, `.env.example` | `app/llm/router.py` | `2` | optional default observed | router/concurrency setup |
| `JWT_SECRET` | `app/config.py:40`, `.env.example` | `app/security/auth.py` | `change-me` | default observed; production boot checks presence/length | `Settings.validate_boot` |
| `MCP_TOKEN_PEPPER` | `app/config.py:43`, `.env.example` | MCP/API token hashing in `app/security/auth.py` | `change-me` | default observed; production boot checks presence/length | `Settings.validate_boot` |
| `OIDC_ENABLED` | `app/config.py:108`, `.env.example` | `app/api/routes_oidc.py` | `false` | optional default observed | `Settings.validate_data_runtime_policy` conditional branch |
| `OIDC_ISSUER` | `app/config.py:109`, `.env.example` | OIDC route/client | empty | conditional field observed | OIDC boot validation |
| `OIDC_CLIENT_ID` | `app/config.py:110`, `.env.example` | OIDC route/client | empty | conditional field observed | OIDC boot validation |
| `OIDC_CLIENT_SECRET` | `app/config.py:111`, `.env.example` | OIDC route/client | empty | conditional field observed | OIDC boot validation |
| `OIDC_REDIRECT_URI` | `app/config.py:112`, `.env.example` | OIDC callback route | empty | conditional field observed | OIDC boot validation |
| `SESSION_SECRET` | `app/config.py:113`, `.env.example` | OIDC session middleware | `change-me-session` | default observed; conditional boot validation | `Settings.validate_data_runtime_policy` |
| `CORS_ALLOW_ORIGINS` | `app/config.py:118`, `.env.example` | `Settings.cors_origin_list`, API middleware | empty | optional default observed | property parsing |
| Tenant/RLS-specific env variables | No explicit `TENANT_*`/`RLS_*` setting found in requested config files | RLS uses identity/database paths (`app/security/rls.py`, `app/security/auth.py`) | NEED FILE/CONTEXT for an env variable | no explicit env contract observed | NEED FILE/CONTEXT |

## Dependency summary

| Category | Evidence and relevant dependencies/services |
|---|---|
| Backend runtime | FastAPI, Uvicorn, Pydantic/Pydantic Settings, multipart upload support (`pyproject.toml`) |
| Database/vector/migrations | SQLAlchemy async, asyncpg, pgvector, Alembic; PostgreSQL pgvector service in compose |
| Auth/security | python-jose, passlib, bcrypt, Authlib, itsdangerous |
| Ingestion/RAG | pypdf, tiktoken, defusedxml, PyYAML; optional local extra: docling, sentence-transformers, FlagEmbedding |
| Agent/LLM | pydantic-ai-slim, httpx, openai; local/cloud-compatible router in `app/llm/router.py` |
| Worker/queue | arq and redis; Redis compose service |
| MCP/observability | mcp, prometheus-fastapi-instrumentator, OpenTelemetry SDK/instrumentation/exporter |
| Development/test | pytest, pytest-asyncio, ruff, mypy, optional ragas |
| Frontend runtime | React, React DOM, React Router, Zustand, react-markdown, Mermaid, KaTeX, react-force-graph |
| Frontend build/dev | TypeScript, Vite, Vite React plugin, Tailwind/PostCSS, related type/highlight packages |
| External services | PostgreSQL/pgvector, Redis, optional local OpenAI-compatible LLM (commented vLLM service), Caddy in prod compose, optional Keycloak and observability overlays |
| Lock/build inputs | `uv.lock`, `frontend-react/package-lock.json`, `Dockerfile` multi-stage Node 20 + Python 3.11 |

## Test command baseline

| Purpose | Command | Source of command | Executed | Exit code/result | Notes |
|---|---|---|---|---|---|
| All backend tests | `pytest -q` | `.github/workflows/ci.yml`, `README-DEV.md` | No | NEED FILE/CONTEXT: host Python/pytest unavailable | CI runs with a Postgres service |
| Test collection | `pytest --collect-only -q` | Standard pytest collection form; no repository-specific script observed | No | NEED FILE/CONTEXT: pytest unavailable | Collection command not documented verbatim |
| RLS/security tests | `pytest -q tests/test_rls.py tests/test_memory_rls.py tests/test_sensitivity.py tests/test_router_egress.py` | Test file inventory | No | NEED FILE/CONTEXT: pytest unavailable | Path-targeted subset |
| Agent tests | `pytest -q tests/test_agent_loop.py tests/test_agent_runs.py tests/test_chat.py tests/test_mcp_server.py` | Test file inventory | No | NEED FILE/CONTEXT: pytest unavailable | Path-targeted subset |
| RAG/ingestion tests | `pytest -q tests/test_grounding.py tests/test_ingestion_wpa.py tests/test_mock_source.py tests/test_egress_embedding.py` | Test file inventory | No | NEED FILE/CONTEXT: pytest unavailable | Path-targeted subset |
| Accounting/tax tests | `pytest -q tests/test_accounting_rules.py tests/test_ap_*.py tests/test_coa.py tests/test_journal*.py tests/test_tax.py` | Test file inventory | No | NEED FILE/CONTEXT: pytest unavailable | PowerShell wildcard expansion may be needed on Windows |
| Eval/readiness tests | `pytest -q tests/test_eval_passk.py tests/test_bravo_*.py` | Test file inventory | No | NEED FILE/CONTEXT: pytest unavailable | Path-targeted subset |
| Deterministic eval gate | `python -m app.eval.run --passk --mock --k=8` | `.github/workflows/ci.yml` | No | NEED FILE/CONTEXT: Python unavailable | CI hard-gate command |
| Frontend build/type check | `cd frontend-react && npm run build` | `frontend-react/package.json`, README | No | NEED FILE/CONTEXT: npm unavailable | Script runs `tsc --noEmit && vite build` |
| Frontend dev server | `cd frontend-react && npm run dev` | `frontend-react/package.json`, README | No | NEED FILE/CONTEXT: npm unavailable | Development command, not a test |
| Lint | `ruff check app` | `.github/workflows/ci.yml` | No | NEED FILE/CONTEXT: ruff unavailable | CI blocking step |
| Type check | `mypy app` | `mypy` dev dependency; no CI invocation observed | No | NEED FILE/CONTEXT: mypy unavailable | Command is a tool baseline, not repository CI evidence |
| Migration validation | `alembic upgrade head` | `.github/workflows/ci.yml`, `deploy/bootstrap.sh`, README | No | NEED FILE/CONTEXT: alembic unavailable | Requires PostgreSQL/pgvector service |

## Required file coverage

| Group | Observed paths | Coverage |
|---|---|---|
| API/security | `app/main.py`, `app/api/`, `app/security/`, `app/config.py`, `app/ratelimit.py` | Present |
| Database/RLS/memory | `app/database/`, `alembic/`, `app/security/rls.py`, `app/agent/memory.py` | Present; `migrations/` alias absent |
| RAG/ingestion | `app/rag/`, `app/ingestion/`, `scripts/ingest_userguide.py`, `file_system/bravo_corpus_manifest.yaml` | Present |
| Agent/tools | `app/agent/`, `app/llm/router.py`, `app/mcp/server.py`, `app/agent/tools.py` | Present |
| Accounting/ERP | `app/accounting/`, `app/erp/`, `app/agent/tax.py`, `app/agent/anomaly.py`, `app/accounting/data/` | Present |
| Eval | `app/eval/`, `tests/eval/`, `app/eval/golden_set.example.yaml`, `file_system/bravo_lifecycle_playbooks.yaml`, `file_system/bravo_ai_use_cases.yaml` | Present |
| Deployment | `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`, `deploy/`, `.env.example`, `scripts/backup.sh` | Present; no separately named restore script observed (`NEED FILE/CONTEXT`) |
| Frontend | `frontend-react/src/`, `src/api/client.ts`, `src/api/types.ts`, `src/api/sse.ts`, `vite.config.ts` | Present; no frontend `.env` file or test script observed (`NEED FILE/CONTEXT`) |
| CI | `.github/workflows/ci.yml` | One workflow observed |

## Runtime/artifact path candidates

| Path | Observed contents | Referenced by | Candidate classification | Needs deeper review |
|---|---|---|---|---|
| `app/` | Python source modules | Packaging/Docker and imports | source code | No for T0; subsystem tasks inspect scoped files |
| `frontend-react/src/` | React/TypeScript source | Vite build and API client | source code | T8 |
| `file_system/` | BRAVO PDFs, DOCX, YAML, Markdown | `CORPUS_ROOT`, ingestion/eval defaults | shared corpus candidate | T3/T6 |
| `file_system/Data/` | Operational/sample Markdown/XML | Runtime policy and routes | private operational/sample candidate | T2/T3/T6 |
| `file_system/Mindmaps/` | Markdown mindmaps | Corpus/document references | derived summary candidate | T3 |
| `file_system/bravo_corpus_manifest.yaml` | Manifest entries for corpus files | `scripts/ingest_userguide.py`, `app/ingestion/manifest.py`, eval | corpus manifest | T3 |
| `file_system/bravo_lifecycle_playbooks.yaml` | Playbook YAML | `app/agent/bravo_playbooks.py`, eval | policy/playbook | T4/T7 |
| `file_system/bravo_ai_use_cases.yaml` | Use-case YAML | `app/agent/bravo_use_cases.py`, eval | policy/use-case data | T4/T7 |
| `file_system/bravo_data_runtime_policy.yaml` | Runtime classification/path rules | `app/config.py`, `app/eval/bravo_data_policy.py` | runtime policy | T2/T6 |
| `app/accounting/data/` | Statutory/mapping/COA YAML | accounting governance/engines | domain rules | T5 |
| `data/uploads/` | Existing runtime upload directory (observed empty directory) | `app/api/routes_sources.py`, `UPLOAD_ROOT` | runtime uploads | T2/T6 |
| `data/private/` | Existing private data directory (observed empty directory) | `PRIVATE_DATA_ROOT` and policy | private operational data | T2/T6 |
| `tests/fixtures/` | Invoice and mock financial fixtures | pytest/eval | test fixtures | T7 |
| `scratch_test/`, `scratch_multipart/` | Scratch project/directory names | file inventory only | temp/scratch candidate | NEED FILE/CONTEXT |
| `frontend-react/dist/` | Build output path referenced by Docker/app; not present in inventory | Docker multi-stage and `app/main.py` | generated frontend artifact | T8 |
| Cache/index paths | No dedicated generated index/cache directory observed from file/path scan | RAG modules use runtime/library caches; no path contract located | generated index/cache candidate | NEED FILE/CONTEXT |
| `docs/`, `docs/research/` | Architecture, ADR, runbooks, research/findings | human/reference consumers | research/docs | T1–T8 use only scoped references |

## Commands executed

| Command/probe | Exit code/result |
|---|---|
| `git rev-parse --show-toplevel; git branch --show-current; git rev-parse HEAD; git status --short` | 0; metadata recorded above |
| Host version probe for `python`, `py`, `node`, `npm`, `uv`, `alembic`, `pytest`, `ruff`, `mypy`, `docker` | 0 as a probe; `node` returned `v24.16.0`; Python/npm/uv/alembic/pytest/ruff/mypy/docker were not found |
| `rg --files` inventory excluding common dependency/build/cache directories | 0; file inventory collected |
| PowerShell directory tree probe (depth ≤5, excluded paths) | 0; tree recorded above |
| `Get-Content pyproject.toml`, `frontend-react/package.json`, `Dockerfile`, compose files | 0 for readable files; dependency/entrypoint evidence recorded |
| `rg` config-variable and entrypoint/reference probes | 0 for completed probes; matched paths/symbol references recorded |
| `.github/workflows` and required-path existence probes | 0; `ci.yml` and coverage table recorded |
| Runtime policy, corpus manifest header, data-directory listing | 0; path candidates recorded |
| Frontend env/build-file probe | 1 for the second `rg` subprobe with no matching env-variable text; existing config/package paths and `VITE_DEMO_LOGIN` reference were recorded |
| `New-Item -ItemType Directory -Force docs/reviews/2026-07` | 0; created output directory |

## Missing evidence

- Host Python toolchain and Python packages are unavailable; no test, lint, type-check, migration, or eval command was executed.
- Host npm CLI is unavailable; no frontend build/type-check was executed. No frontend test runner/script was observed in `frontend-react/package.json`.
- No separately named restore script was found; only `scripts/backup.sh` is present.
- No explicit `TENANT_*` or `RLS_*` environment variable definition was observed; tenant/RLS context is represented by code/database identity paths and requires scoped review.
- No dedicated generated index/cache path contract was found from the inventory scan.
- `migrations/` and root-level `bravo_corpus_manifest.yaml` paths are absent; equivalent paths are `alembic/` and `file_system/bravo_corpus_manifest.yaml`.

## Handoff to T1–T8

| Task | Recommended input paths | Important references | Missing context |
|---|---|---|---|
| T1 API/auth/security | `app/main.py`, `app/api/`, `app/security/`, `app/config.py`, `app/ratelimit.py` | `tests/test_admin.py`, `test_auth` if present, `.env.example` | Runtime identity/IdP deployment values |
| T2 database/RLS/memory | `app/database/`, `alembic/`, `app/security/rls.py`, `app/agent/memory.py` | `tests/test_rls.py`, `tests/test_memory_rls.py`, `DATABASE_URL` | Live PostgreSQL/RLS session context |
| T3 RAG/ingestion | `app/rag/`, `app/ingestion/`, `scripts/ingest_userguide.py` | `file_system/bravo_corpus_manifest.yaml`, runtime policy, ingestion tests | Actual model/index runtime and corpus selection |
| T4 agent/tools/MCP | `app/agent/`, `app/mcp/server.py`, `app/llm/router.py` | `tests/test_agent_loop.py`, `test_mcp_server.py`, playbooks/use-cases YAML | Runtime tool permissions and model responses |
| T5 accounting/ERP/tax | `app/accounting/`, `app/erp/`, `app/agent/tax.py`, `app/agent/anomaly.py` | `app/accounting/data/`, accounting/AP/tax tests | ERP endpoint/credential contract |
| T6 egress/deployment/operations | `.env.example`, `app/config.py`, compose files, `Dockerfile`, `deploy/` | `app/observability.py`, `app/llm/router.py`, CI | Deployed secrets, external endpoints, restore procedure |
| T7 eval/readiness | `app/eval/`, `tests/eval/`, `tests/test_bravo_*.py` | CI pass-k command, golden sets, policy/playbook YAML | Executable environment and CI artifacts |
| T8 frontend/contracts | `frontend-react/src/`, `package.json`, `vite.config.ts` | `src/api/client.ts`, `types.ts`, `sse.ts`, API routes | Frontend test tooling and runtime `VITE_*` configuration |
