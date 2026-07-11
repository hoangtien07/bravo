# T1 — API/Auth/Security Boundary

Scope read: `app/main.py`, `app/api/**`, `app/security/**`, `app/config.py`, `app/ratelimit.py`, and direct API dependencies (`app/observability.py`, `app/database/__init__.py`, `app/mcp/server.py`). Evidence below is from current implementation and tests only; no test command was run because the host Python toolchain is unavailable (T0).

## Request and auth flow

| Stage | Implementation evidence | Context carried forward |
|---|---|---|
| HTTP entry | `app/main.py:app` mounts aggregate router at `/api`; mounts MCP separately at `/mcp` when created | Request and optional bearer header |
| Login | `routes_auth.login` looks up `Employee` by form username, verifies password, and returns JWT with `sub=employee_id` | JWT only carries employee ID and expiry (`security.auth.create_access_token`) |
| JWT principal | `security.auth.get_current_identity` decodes JWT, loads `Employee`, then calls `_employee_to_identity` | `Identity(employee_id, department_ids, permissions, is_admin)` |
| Route authorization | `require_permission` calls `Identity.scope_level(resource, action)`; `require_admin` checks `is_admin` | Same `Identity` injected into route and direct service consumers |
| Scope enforcement handoff | Read routes pass `Identity` to retrieval/source/draft/agent consumers; `source_scope_filter` and `conversation_scope_filter` are API-adjacent predicates | T2 verifies database/RLS predicates; T4 verifies agent session/tool consumers |
| OIDC principal | `routes_oidc.oidc_callback` maps IdP email to `Employee`, creates a non-admin account if absent, then returns an internal JWT in a URL fragment | Current implementation does not add a per-request site/tenant value to `Identity` |
| MCP principal | `mcp.server.search_kb` extracts a bearer token, resolves it by HMAC digest to `Identity`, then calls retrieval | Separate bearer-token auth path; T4 reviews tool boundary |

`Settings.site_config` is startup configuration; no site/tenant field is present in `Identity` or in API dependency parameters. Department scope enters the request path only from the database-backed `Employee.department_ids` used to construct `Identity`.

## Route boundary map

| Boundary | Auth behavior observed | Principal/scope consumer |
|---|---|---|
| Public operational routes | `/livez`, `/readyz`, `/health`; `/metrics` is exposed when metrics are enabled | No `Identity` dependency |
| Public auth routes | `/api/auth/login`, `/api/auth/config`, OIDC login/callback | Login resolves credentials/IdP flow; config returns only OIDC enabled flag |
| JWT-protected reads | `/api/me`, sources, graph, ask, agent ask, conversation CRUD | `get_current_identity` or `require_permission("doc:read")` |
| JWT-protected writes | source upload, invoices/drafts, agent scan/reconcile, draft actions | `require_permission("doc:create" | "draft:create" | "draft:approve")` and direct service call |
| Admin boundary | `/api/admin/*` | `require_admin` (except self password change, which binds to current identity) |
| Capability-share boundary | `GET /api/shared/{token}` | No JWT; `shared_token` lookup returns read-only conversation data |
| CORS/session boundary | CORS added only if configured origins are non-empty; OIDC session middleware only if OIDC is enabled | `Settings.cors_origin_list`, `Settings.session_secret` |
| Rate-limit boundary | SlowAPI middleware is enabled when configured, but only chat streaming has `@limiter.limit` | `routes_conversations.chat_stream` |

## Findings

| ID | Severity tạm thời | Evidence state | File:symbol | Evidence ngắn | Consumer/impact | Next action | Needs Sol review |
|---|---|---|---|---|---|---|---|
| BRV-API-001 | Medium | VERIFIED | `app/security/rls.py:Identity.scope_level`; `app/api/routes_admin.py:ASSIGNABLE_PERMISSIONS` | `scope_level` accepts only `<resource>:<action>:all` or `:own_dept`; the admin assignment list includes bare `doc:create`, `metric:read`, `draft:create`, and `draft:approve`. Routes require those bare forms, which are parsed through `scope_level`. | Non-admin accounts assigned these listed values receive 403 on source, draft, invoice, and agent-scan routes; permission policy is inconsistent across API/T4/T5 consumers. | Normalize the permission vocabulary and add an authorization test for every assignable permission against its intended route. | No |
| BRV-API-002 | High (conditional) | INFERRED | `app/api/routes_sources.py:upload_source` | Caller-controlled `department_ids` is converted directly to `SourceDepartment` rows. The route does not compare requested IDs with `identity.department_ids` or `identity.scope_level("doc", "create")`. | If any deployed account has `doc:create:own_dept` (the scope vocabulary supported by `Identity`), it can submit arbitrary department IDs or empty/global scope. This crosses private/shared data and RLS boundaries; current employee permission records were not available. | T2 verify source/RLS write invariants and deployed permission records; T3 verify ingestion preserves source scope. Confirm severity with Sol before remediation. | Yes |
| BRV-API-003 | Medium | VERIFIED | `app/ratelimit.py:limiter`; `app/api/routes_conversations.py:chat_stream`; `routes_ask.ask`; `routes_agent.agent_ask` | The only `@limiter.limit(...)` use in `app/` is on streaming chat. `/api/ask` and `/api/agent/ask` call retrieval/LLM or `AgentSession` without an endpoint limit; agent scan/reconcile routes are also un-decorated. | Authenticated callers can invoke expensive API paths without the configured per-route limiter. Consumer impact includes LLM, retrieval, agent, and DB capacity. | Define intended rate-limit coverage by endpoint class and add HTTP tests for enforced 429 behavior; T4/T6 validate downstream cost and deployment controls. | No |
| BRV-API-004 | Medium | VERIFIED | `app/main.py:readyz` | Public `/readyz` catches a database exception and returns `str(exc)` in `checks["db"]` with a 503 response. | An unauthenticated caller can receive deployment/database error detail when readiness fails. | Return a stable external health status; preserve detailed error only in server logs. T6 verify reverse-proxy exposure. | No |
| BRV-API-005 | Low | VERIFIED | `app/observability.py:setup`; `app/main.py:_obs_setup` | `main` unconditionally calls observability setup; with default `metrics_enabled=True`, `Instrumentator().expose(app, endpoint="/metrics")` installs a route without an auth dependency. | Metrics are available to any network client that can reach the application; content includes request/process metrics and BRAVO LLM/tool metric names. | T6 verify network policy and decide whether application-level protection is required; add an exposure test for the chosen policy. | No |
| BRV-API-006 | Low | VERIFIED | `app/api/routes_sources.py:upload_source`; `routes_invoices.invoice_to_draft`; `routes_conversations.chat_stream` | Each serializes raw exception text to the client (`Ingest failed: {exc}`, invoice processing error, SSE `{message: str(exc)}`). | Authenticated callers can receive implementation/downstream error detail; stream errors are delivered after the response begins. | Replace client messages with stable error codes/request IDs and log exception detail server-side; T4/T5/T6 assess the downstream exception sources. | No |

## Test evidence and gaps

| Evidence | State | Relevance |
|---|---|---|
| `tests/test_http_health.py:test_unauthenticated_protected_route_rejected` checks that the invoice route rejects a request without auth (401 or validation 422). | VERIFIED (not executed in this environment) | Basic protected-route coverage |
| `tests/test_admin.py:test_non_admin_forbidden` checks a non-admin gets 403 from `/api/admin/users`; the same file checks assignment of `doc:read:own_dept`. | VERIFIED (not executed) | Admin and scoped read-path coverage |
| `tests/test_rls.py` covers `doc:read:own_dept` and `doc:read:all` in `Identity`/source scope logic. | VERIFIED (not executed) | Confirms the scoped permission vocabulary used by BRV-API-001/002 |
| No scoped test was found for source-upload department IDs, API rate-limit coverage beyond chat, public readiness error content, public metrics exposure, or raw exception serialization. | VERIFIED by scoped test-name/reference scan | Add coverage with the related remediation; lack of a test alone is not a production finding. |

## Handoff

| Task | Input/decision handed off | Evidence state |
|---|---|---|
| T2 — Database/RLS/memory | Verify BRV-API-002 against `Source`, `SourceDepartment`, write-time constraints, and actual `Employee.permissions`; verify routes that pass `Identity` to scope predicates. | NEED FILE/CONTEXT for deployed records; implementation gap identified |
| T3 — RAG/ingestion | Verify whether a source's caller-supplied department assignments are retained through ingest/chunk/retrieval. | NEED FILE/CONTEXT from ingestion scope propagation |
| T4 — Agent/tools/MCP | Verify `AgentSession` handling of API-provided `session_id`, agent/tool authority, and MCP scope resolution. | NEED FILE/CONTEXT beyond direct API call sites |
| T5 — Accounting/ERP | Verify permission mismatch effects on draft/invoice endpoints and raw exception sources from accounting/draft services. | VERIFIED API entry evidence; service behavior not reviewed here |
| T6 — Egress/deployment/operations | Verify external reachability and policy for `/metrics`, `/readyz`, CORS origins, rate-limit configuration, and error logging. | NEED FILE/CONTEXT for deployment/network controls |

## Missing context

- Current `Employee.permissions` rows and any out-of-band permission provisioning were not available; they determine the runtime reachability of BRV-API-002 and the extent of BRV-API-001.
- Reverse-proxy/firewall policy was not read in this task; application-level public routes may be network-restricted in deployment.
- This task did not inspect RLS/database implementation in depth, agent/tool execution, ingestion propagation, or ERP/accounting service behavior.
