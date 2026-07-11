# T11 — Independent Database Isolation Architecture

## Executive decision

- Select **Option D: Hybrid application authorization/predicates + PostgreSQL RLS backstop + separated admin/migration roles**.
- Decision status: **Adopt incrementally**. Native enforcement starts only after scope normalization, transaction-local context, role separation, and negative tests; Phase 0 application fixes proceed immediately and independently.
- Enforce the dimensions that exist now: department, user/owner, and explicit shared records. Tenant/site are not present in the reviewed identity or schema and are not invented by this ADR.
- Use immutable principal metadata on each `AsyncSession` and transaction-local PostgreSQL settings reapplied at every transaction begin. No session-scoped tenant state and no implicit global system jobs are allowed.
- PostgreSQL enforces row visibility and write scope; application services still enforce permissions, maker-checker, approval state, journal/number integrity, and all T10 pilot-blocker fixes.

## Current-state evidence

| Evidence state | File:symbol | Observed state | Architecture consequence |
|---|---|---|---|
| VERIFIED | `app/database/__init__.py:engine, async_session_factory, get_db` | HTTP, MCP, and worker paths use one async engine/session factory from one `DATABASE_URL`; no principal binding, role switch, or unit-of-work wrapper exists. | A context-bound session abstraction and path-specific credentials are required before native policies can be enforced. |
| VERIFIED | `app/security/rls.py:Identity` | Identity contains employee ID, department IDs, permission strings, and admin flag. No tenant or site field exists. | Initial DB policy dimensions are department and owner only; tenant/site require a later schema/identity migration if business evidence demands them. |
| VERIFIED | `app/security/rls.py:*_scope_filter`; T10 `BRV-DATA-001` | Reviewed application reads use explicit SQL predicates; PostgreSQL has no native row-policy backstop. | Keep predicates as primary, testable authorization and add RLS for omitted-query defense. |
| VERIFIED | `alembic/versions/0004_db_roles.py:upgrade` | `bravo_agent`/`bravo_writer` are NOLOGIN roles, but the two `app_safe` views are unfiltered `SELECT *`; the migration states the app still uses a DBA connection. | Existing roles/views are not independent row isolation and must not be treated as such. |
| VERIFIED | `app/database/models.py:Source, SourceDepartment, Chunk, Draft` | Sources use absence of mappings, chunks use an empty UUID array, and drafts use NULL to mean global. | Current global representation is fail-open on omission; explicit scope type and legacy-data classification are prerequisites to write-time RLS. |
| VERIFIED | `app/database/models.py:Conversation, ConversationMessage, MemoryBlock, AgentRun` | Conversation has `employee_id`; message/block tables have only `session_id`; AgentRun has both session and employee IDs. No DB foreign key anchors memory rows to a session owner. | Owner isolation needs an authoritative session-owner anchor and orphan/backfill checks before policy enablement. |
| VERIFIED | `app/security/auth.py:get_current_identity, resolve_mcp_identity` | HTTP loads an Employee by JWT subject; MCP finds an Employee by token hash before protected retrieval. | HTTP can bind context from verified JWT subject; MCP needs a narrow bootstrap resolver followed by a fresh context-bound transaction. |
| VERIFIED | `app/mcp/server.py:kb_search` | MCP opens the shared session factory, resolves token, and retrieves in that session. | MCP should use a read-only runtime credential and must not perform protected reads before context binding. |
| VERIFIED | `app/worker.py:ingest_task` | Worker job contains `source_id` and `path`, but no initiating user or service principal. | Worker execution must fail closed until the job envelope carries an explicit principal/capability and current authorization is re-resolved. |
| VERIFIED | agent memory/run/conversation services and `app/erp/draft_queue.py` | Services commit and sometimes roll back internally; one request or agent turn can start several DB transactions. | Setting context once at request entry is insufficient. Context must be reapplied on every transaction begin while service-level commits are gradually removed. |
| VERIFIED | T10 `BRV-BIZ-002` | Draft approve/reject omits object scope at the service query. | The direct predicate fix and test are Phase 0 work; RLS is an additional backstop, not its prerequisite or replacement. |
| NEED FILE/CONTEXT | deployed PostgreSQL metadata | Actual login role, ownership, grants, BYPASSRLS, policies, and default privileges were not inspected. | Run a non-mutating privilege inventory before DBISO-02 and before any production cutover. |
| NEED FILE/CONTEXT | production data | Intent of existing NULL/empty scopes and the count of orphan session/memory rows are unknown. | No automatic “legacy NULL = shared” migration is permitted. Ambiguous rows must be quarantined or explicitly classified. |

## Decision matrix

Scores use 1 (weak/poor fit) to 5 (strong/good fit). Security criteria are minimum gates, not interchangeable with ease or performance scores.

| Criterion | A. Predicates only | B. Roles + predicates | C. Native RLS + context | D. Hybrid RLS + predicates |
|---|---:|---:|---:|---:|
| Cross-department isolation | 3 | 3 | 5 | 5 |
| Defense against omitted predicates | 1 | 2 | 5 | 5 |
| Write-time scope enforcement | 2 | 3 | 5 | 5 |
| Async pooling compatibility | 5 | 5 | 3 | 4 |
| Agent/MCP/worker fit | 4 | 4 | 3 | 4 |
| Ease of testing | 3 | 4 | 3 | 4 |
| On-prem operation | 5 | 5 | 5 | 5 |
| Migration risk | 5 | 4 | 2 | 3 |
| Rollback | 5 | 4 | 2 | 3 |
| Operational ownership | 5 | 4 | 3 | 3 |
| Performance | 5 | 5 | 4 | 4 |
| Auditability | 2 | 4 | 5 | 5 |
| **Total / 60** | **45** | **47** | **45** | **50** |

| Option | Isolation strength | Pooling safety | Worker/MCP fit | Migration effort | Operational complexity | Performance | Failure mode | Recommendation |
|---|---|---|---|---|---|---|---|---|
| A. Application predicates only | Existing department/owner filtering, but query-by-query | High because no DB context | Current paths fit | Low | Low | Current baseline | One omitted predicate exposes every row granted to the runtime role | Reject: does not satisfy independent isolation. |
| B. Separate least-privilege roles + predicates | Limits tables/actions, not rows within the same table | High | Good with separate credentials | Medium | Medium | Near baseline | Omitted predicate still exposes all rows in a granted table; existing views demonstrate this weakness | Defer as final model; adopt its role separation as part of D. |
| C. PostgreSQL RLS with transaction-local context | Strong row/write backstop | Safe only with per-transaction binding | Requires principal-aware jobs/MCP bootstrap | High | High | Policy overhead; index-sensitive | Missing context can fail closed, but app business authorization and typed validation may be mistakenly removed | Reject as standalone: RLS cannot replace route/tool/business semantics. |
| D. Hybrid RLS + application predicates | Strongest defense against both bad application queries and policy misconfiguration detectable by dual tests | Safe with the transaction contract below | Fits after explicit principal envelopes and path roles | High but phased | Medium-high | Expected modest overhead if predicates remain indexable | Mixed-version clients without context see zero rows/write errors; policy drift can cause false denial | **Selected; Adopt incrementally.** |

Why D despite its rollout cost:

- `BRV-DATA-001` shows an omitted-predicate backstop is absent, while `BRV-BIZ-002` shows such omissions are realistic in a state-transition service.
- Option B reduces blast radius by table/action but cannot isolate departments within `drafts`, `chunks`, or memory tables.
- Option C alone would centralize row scope but cannot decide whether a user may approve, publish shared content, export a voucher, or pass a number-integrity gate.
- The repository already has application predicates and PostgreSQL-specific arrays/vector indexes, so retaining those predicates while adding equivalent RLS has lower behavioral risk than replacing them.

## ADR-DB-001

### ADR-DB-001 — Independent database isolation model

- Status: **Accepted — Adopt incrementally**
- Related findings:
  - `BRV-DATA-001` — final Medium; motivates defense-in-depth.
  - `BRV-BIZ-002` — final High; direct application fix is mandatory and independent.
  - `BRV-DATA-002` — Need more evidence; direct session ownership guard is allowed and recommended without assuming disclosure is confirmed.
- Context: BRAVO uses application-side SQL predicates for department/owner scope, a shared async session factory, and PostgreSQL-specific persistence. Current database roles do not enforce row scope. HTTP, agent, MCP, and worker access need a common fail-closed data boundary without moving business decisions into PostgreSQL.
- Current evidence: Department and user/owner are implemented dimensions. Tenant/site are absent. Global state is encoded by omission. Protected-path services may commit multiple times, MCP bootstraps identity inside a DB session, and worker jobs have no principal.
- Options considered: A application predicates only; B separate least-privilege roles plus predicates; C native PostgreSQL RLS plus transaction-local context; D hybrid RLS plus application predicates and separated operational roles.
- Decision: Adopt D incrementally. Keep application authorization and repository predicates; add least-privilege runtime roles, transaction-local principal context, `ENABLE ROW LEVEL SECURITY` plus `FORCE ROW LEVEL SECURITY` on protected tables, and explicit admin/migration/backup bypass roles.
- Why: D is the only option that independently blocks an omitted row predicate while preserving route/tool permissions and financial safety validation. It also permits canary rollout: roles and context can be introduced before policy enforcement.
- Components affected: SQLAlchemy session/UoW setup; auth bootstrap; PostgreSQL roles/default privileges; Alembic policy migrations; source/chunk scope schema; draft scope schema; conversation/session ownership; MCP DB bootstrap/pool; worker job envelopes/pool; RLS/object-scope tests; backup/restore verification.
- Database roles: `bravo_owner`, `bravo_app_runtime`, `bravo_mcp_runtime`, `bravo_worker_runtime`, `bravo_migrator`, `bravo_diagnostics`, `bravo_backup`, `bravo_breakglass`, and ephemeral CI equivalents, as constrained below.
- Principal context contract: Bind immutable `principal_kind`, `principal_id`, optional delegated `actor_employee_id`, `auth_source`, and `request_id` to the AsyncSession. At every transaction begin call PostgreSQL `set_config(..., true)`. Department membership, admin status, and shared-publisher capability are derived by hardened DB helper functions from canonical tables, not trusted from request arrays/GUC booleans.
- Transaction/pooling contract: One principal per AsyncSession; explicit short transactions; context reapplied at every transaction begin; commit/rollback/cancellation ends transaction-local state; no session reuse across principals; no open DB transaction across LLM/network streaming; pool return always rolls back an unfinished transaction.
- HTTP behavior: Decode/verify token in application, bind JWT employee subject before the first protected query, load current Employee/permissions under self-context, then execute route work. Missing/invalid context fails closed.
- Agent behavior: AgentSession inherits the authenticated user context but does not hold one transaction across retrieval, LLM, tools, or streaming. Each DB phase uses a new short transaction bound to the same immutable principal. Resumed runs re-resolve current permissions.
- MCP behavior: Resolve token hash through a narrow bootstrap function/transaction that returns only principal ID; close it; open a read-only MCP session with that principal and apply RLS before retrieval. Invalid/revoked token fails before any protected read.
- Worker behavior: Every user-triggered job carries initiator principal ID, required capability, source/resource ID, request/job ID, and auth source. Worker re-resolves current authorization at execution. Scheduled jobs use registered service principals with explicit department/capability grants; missing principal/capability fails closed.
- Migration/admin behavior: Runtime never owns tables or has BYPASSRLS. Migrations use a controlled migrator that can assume the NOLOGIN owner role for DDL. Normal admin routes remain subject to RLS with DB-derived admin capability. Full-data backup and break-glass are explicit audited bypasses outside request paths.
- Shared/global record semantics: Replace absence-as-global with explicit `scope_kind`. `shared` requires a DB-derived publish capability; `department` requires at least one authorized mapping; `owner` requires a matching owner. Ambiguous legacy NULL/empty rows are not auto-shared.
- Consequences: Omitted application predicates are contained by PostgreSQL; authorization is tested twice; DB and app policy drift can produce false denial; deployment/runbook and test complexity increase; context/role migrations become release-sensitive.
- Risks: Mixed-version clients without context fail closed; security-definer helpers can become privilege escalation points; policy expressions can degrade vector/search plans; legacy scope backfill can misclassify data; app-supplied principal ID remains a trusted authentication assertion and RLS does not defend against total application credential compromise.
- Rollout: Four phases, described below. Phase 0 T10 fixes starts immediately. RLS is enabled only after context-aware binaries and shadow/negative tests are complete.
- Rollback: Retain application predicates and normalized scope columns. Revert enforcement to restricted-role-plus-predicates by disabling/NO FORCE RLS through the migrator if necessary; never return the runtime to table-owner/DBA credentials. Use time-bounded break-glass only for controlled recovery.
- Required tests: All 18 tests below, including the 12 mandated isolation cases, pooling/transaction hardening, policy parity, and performance validation.
- Performance validation: Compare current predicate-only and hybrid plans using representative production cardinality. Preserve GIN/HNSW/FTS usage; cache effective departments once per statement through `STABLE` helpers; target p95 read overhead at or below 10%, and block rollout above 20% or on material retrieval-recall loss until optimized.
- Operational owner: Joint ownership: PostgreSQL/platform owner for roles, policies, backup, and break-glass; application security owner for principal/UoW contract; subsystem owners for repository predicates; accounting control owner for financial service invariants.
- Revisit trigger: Addition of tenant/site columns, direct ERP mutation, a new DB access path, evidence of SQL injection/credential compromise, policy overhead above threshold, inability to anchor every session to an owner, or a requirement that the database independently validate authentication tokens.

### Exact enforcement split

| Layer | Enforces | Does not replace |
|---|---|---|
| Application auth/routes/tools | JWT/MCP authentication, route permission, tool capability, service intent, explicit repository predicates, safe error behavior | Database row/write scope |
| PostgreSQL grants + RLS | Table/action least privilege, department/owner/shared row visibility, `USING` transitions, `WITH CHECK` writes, append-only audit writes, scope consistency backstop | Maker-checker, accounting meaning, approval state, number integrity, export eligibility |
| Business services | Maker-checker, self-approval prohibition, voucher state machine, payload/hash validation, journal schema, deterministic numbers, approved-only export | Independent row isolation |
| Audit/operations | Principal/request correlation, context-bind events, policy denials, break-glass/backup/migration use, restore verification | Authorization decisions by itself |

## Principal and scope contract

### Isolation units

| Unit | Current evidence | Decision |
|---|---|---|
| Tenant | No tenant field in `Identity` or reviewed models | Not enforced in this rollout. Add only with an explicit identity/schema/backfill migration. |
| Site | No site field in `Identity` or reviewed models | Not enforced in this rollout. Do not map department to site by assumption. |
| Department | Employee mappings; source mappings; chunk/archival arrays; draft department | Primary organizational isolation unit. Multiple departments use OR/overlap semantics for reads; writes require every supplied department to be authorized unless shared-publisher capability is present. |
| User/owner | Employee ID on conversations and AgentRun; owner ID on archival | Primary private/session isolation unit. Conversation, message, memory, and run rows must resolve to one authoritative owner. |
| Shared/global | Currently empty/NULL | Rename semantically to explicit `shared`; creation is privileged, never the result of an omitted mapping/default. |
| Private operational files | Runtime filesystem volumes, not DB rows | RLS protects metadata only. Filesystem/object access must continue to be authorized by the application and deployment controls. |

### Context values

| Context key | Source | Authorization use |
|---|---|---|
| `bravo.principal_kind` | Trusted execution adapter: `user` or `service` | Selects canonical principal table; missing/unknown denies. |
| `bravo.principal_id` | Verified JWT subject, MCP resolver result, or registered service principal | Key for DB-derived membership/capabilities. |
| `bravo.actor_employee_id` | Initiating user for delegated worker jobs; otherwise same as principal where applicable | Audit/delegation only; does not expand scope. |
| `bravo.auth_source` | `jwt`, `oidc`, `mcp`, `worker-delegated`, `scheduled`, `support` | Audit and policy diagnostics only. |
| `bravo.request_id` | HTTP correlation ID or generated job/run ID | Audit correlation only. |

Department IDs, `is_admin`, raw permission arrays, tenant ID, and site ID are **not** accepted as granting GUCs. Hardened `app_security` functions derive effective departments and capabilities from Employee/EmployeeDepartment or service-principal grant tables. A raw app-supplied employee ID remains the authenticated assertion; RLS is a defense against omitted predicates, not a replacement for token verification or protection against total runtime-credential compromise.

Security-definer functions are permitted only for minimal bootstrap/policy helpers. They must be owned by `bravo_owner`, use a fixed `search_path` containing only `pg_catalog` and the security schema, contain no dynamic SQL, return minimal IDs/booleans/UUID arrays, revoke PUBLIC execution, and have direct tests for spoofing and search-path attacks.

## Database role model

| Role | Login/ownership | Privileges | BYPASSRLS / FORCE behavior | Normal use |
|---|---|---|---|---|
| `bravo_owner` | NOLOGIN; owns protected schemas/tables/policies/functions | DDL ownership only through controlled assumption | NOBYPASSRLS; protected tables use FORCE RLS | Assumed by migrator for DDL, never by runtime |
| `bravo_app_runtime` | Dedicated application login or login mapped to NOLOGIN grant role; owns nothing | Minimum DML for HTTP/agent paths; EXECUTE hardened context helpers | NOSUPERUSER, NOBYPASSRLS; subject to FORCE RLS | Normal HTTP and API agent requests |
| `bravo_mcp_runtime` | Separate credential/pool; owns nothing | Read-only protected knowledge tables/views plus MCP bootstrap resolver | NOBYPASSRLS; subject to FORCE RLS | MCP search only |
| `bravo_worker_runtime` | Separate credential/pool; owns nothing | Source/mapping read, chunk/source-status ingestion writes, required audit insert; no financial mutation by default | NOBYPASSRLS; subject to FORCE RLS | User-delegated and registered scheduled ingestion jobs |
| `bravo_migrator` | Controlled operational login; can assume owner for DDL | Alembic DDL, policy creation, grants; no application use | No persistent BYPASSRLS | Deployment migration job |
| `bravo_diagnostics` | NOLOGIN grant role with named operator login | Metadata and security-invoker diagnostic views; raw content excluded by default | NOBYPASSRLS | Read-only support/health investigation |
| `bravo_backup` | Dedicated job login/NOLOGIN grant role | Full read required by logical backup; no application DML | Explicit BYPASSRLS is allowed only here if required by `pg_dump`; network/job restricted and audited | Scheduled backup only |
| `bravo_breakglass` | NOLOGIN emergency role granted temporarily to a named operator | Controlled full data access and repair | Explicit BYPASSRLS; never inherited; time-bounded grant | Approved incident/recovery ticket only |
| CI owner/runtime roles | Ephemeral | Owner runs migrations; runtime roles execute tests | CI runtime must show `rolsuper=false`, `rolbypassrls=false`, no ownership | Disposable CI database |

Role/grant rules:

- Revoke schema/table/function privileges from PUBLIC; set owner default privileges before object creation.
- Runtime roles never own protected tables, inherit owner, receive superuser, or receive BYPASSRLS.
- Grants express table/action capability; RLS expresses row scope. Worker/MCP credentials are not interchangeable with the app credential.
- Existing `app_safe` unfiltered views are removed from the trusted-boundary claim. If retained for compatibility on PostgreSQL 16, make them `security_invoker` and verify underlying FORCE RLS; otherwise query protected base tables through RLS.
- Admin HTTP routes use `bravo_app_runtime`; DB-derived admin permissions may broaden a policy, but they do not change DB role or bypass RLS.
- Backup, restore, break-glass, and migrator role use is logged with operator/job identity and change/ticket ID. None is available to normal request processes.

## Transaction and pooling contract

1. A verified principal is bound once to `AsyncSession.info` and is immutable for that session. A session cannot be rebound to another user/service.
2. Execution adapters own explicit short transactions (`async with session.begin()`). Service methods use `flush()`/return values; they should not own commits after Phase 1.
3. During compatibility rollout, a SQLAlchemy transaction-begin hook reads immutable session info and executes bound-parameter `set_config(key, value, true)` for **every** top-level transaction. This covers current service methods that commit and trigger a new implicit transaction.
4. `local=true` is mandatory. Session-scoped `SET`, `set_config(..., false)`, temporary per-user roles, and mutable connection-global state are prohibited.
5. Missing principal context produces empty allowed-department/capability sets. Protected SELECT returns no rows; protected INSERT/UPDATE/DELETE fails `WITH CHECK`/policy. Context parsing functions return deny on absent/invalid values.
6. Commit, rollback, or cancellation ends transaction-local settings automatically. Session close rolls back any unfinished transaction; pool reset-on-return remains rollback. No correctness claim depends on a custom reset of session-scoped state.
7. Nested SAVEPOINTs inherit the same immutable principal. No nested unit may elevate or change principal; savepoint rollback cannot leave a broader context.
8. Streaming/LLM/tool waits do not hold a database transaction. Authorized data is loaded in a short transaction, then the transaction ends. Later persistence opens another transaction and the hook reapplies the same context.
9. A background task after response never receives the request AsyncSession. It receives a principal-aware job envelope and creates its own context-bound session.
10. Concurrent requests always use distinct AsyncSession objects. Pool connections may be reused only after the prior transaction has ended; required tests force A/B requests onto the same physical connection.
11. MCP bootstrap is a separate narrow transaction/session. Protected MCP retrieval begins only after a principal is resolved and bound.
12. Long-lived agent state is a logical session, not a long-lived DB transaction. Each retrieval, memory write, run checkpoint, draft action, and resume uses a short context-bound transaction and re-resolves current capabilities.

`SET LOCAL ROLE` is not chosen for user scope: per-user PostgreSQL roles do not scale to Employee/department membership and complicate pooling. Separate pools are used only for stable execution roles (`app`, `mcp`, `worker`), not for individual users. Explicit query parameters remain in application predicates but are not the DB backstop. Views are acceptable only as security-invoker compatibility surfaces. Security-definer functions are limited to the hardened bootstrap/helper cases above.

## Execution-path matrix

| Path | Principal | Role | Context | Transaction | Fail behavior |
|---|---|---|---|---|---|
| Normal HTTP request | Verified JWT/OIDC employee subject | `bravo_app_runtime` | `user`, employee ID, auth source, request ID | Context bound before first Employee/protected query; short UoW transactions | Missing/unknown employee or context: 401/deny; DB reads empty/writes fail |
| API agent request | Same authenticated employee; session owner checked directly | `bravo_app_runtime` | Same user context plus agent run/request ID for audit | Separate short transactions for retrieval, memory, run/draft writes; no DB tx across LLM | Missing session ownership/capability: fail before memory; this directly implements `BRV-DATA-002` guard without confirming severity |
| MCP token request | Employee ID returned by narrow token-hash resolver | `bravo_mcp_runtime` | `user`, resolved employee ID, `mcp`, MCP request ID | Bootstrap transaction ends; protected read starts in new context-bound transaction | Missing/revoked token or context: no protected query/result |
| Worker triggered by user action | Initiating employee ID plus required capability/resource in job envelope | `bravo_worker_runtime` | `user` or delegated-service context; actor ID; job/request ID | New short transaction per job phase; current grants re-resolved at execution | Missing principal/capability, revoked user, or inaccessible source: fail job closed; no global fallback |
| Scheduled/system job | Registered service principal with explicit capabilities and department grants | `bravo_worker_runtime` or narrower job role | `service`, service-principal ID, job ID, `scheduled` | One context-bound UoW per batch; bounded batch commits reapply context | Unregistered service or absent scope: fail closed; system never implies global |
| Ingestion job | Initiator or registered ingestion service constrained to the source scope | `bravo_worker_runtime` | Principal plus source/job ID; DB derives allowed departments | Read source scope, write chunks/status in short transactions; scope-mirror checks apply | Cannot ingest inaccessible source or write mismatched/shared chunk scope |
| Support/admin job | Named employee with DB-derived admin/support capability and ticket ID | Normal route uses `bravo_app_runtime`; exceptional offline work uses diagnostics/break-glass | User/support context and correlation/ticket | Normal admin stays RLS-bound; break-glass is a separate controlled session | No implicit bypass; missing approval/ticket denies exceptional job |
| Migration | Deployment identity | `bravo_migrator` assuming `bravo_owner` for DDL | Release/change ID; not an application principal | Alembic transaction/NullPool; data rewrites use explicit controlled procedure | Runtime credential cannot migrate; failure aborts rollout before app switch |
| Backup | Dedicated scheduled backup identity | `bravo_backup` | Backup job ID and retention target in operational audit | Read-only consistent snapshot; no application pool | Credential unavailable to app; failed/incomplete dump alerts and does not claim success |
| Restore | Named recovery operator/job | Isolated restore/migrator credential; break-glass only when approved | Restore ticket/job ID | Restore into isolated target, then verify owner/grants/policies before traffic | Target remains unavailable if policy/catalog verification fails |

No scheduled/support implementation was observed in the scoped repository. Their rows define the required admission contract for future or externally configured jobs; they do not assert those paths currently exist.

## Shared/global record model

### Decision

- Replace implicit “no department means global” with an explicit, non-null `scope_kind`: `department`, `owner`, or `shared`, limited per table.
- New protected rows have no fail-open global default. A missing/invalid scope fails insert.
- `shared` creation requires a DB-derived capability such as `doc:publish_shared`; it is not inferred from `is_admin` alone unless governance explicitly maps admin to that capability.
- Department reads use shared OR overlap with effective departments. Multi-department records are visible on any overlap, matching current application semantics.
- Department writes require every mapped/array department to be in the effective set; an `own_dept` actor cannot attach a foreign department. Shared publisher is the only controlled exception.
- Current NULL/empty records are inventoried and explicitly classified. Ambiguous rows are quarantined as non-readable/non-exportable until an owner approves classification; they are never bulk-converted to shared solely because they are NULL/empty today.

### Table policy semantics

| Data set | SELECT `USING` | INSERT `WITH CHECK` | UPDATE/DELETE | Schema/consistency prerequisite |
|---|---|---|---|---|
| `sources` | `shared` with read permission, or any authorized source department | Creator/principal recorded; `department` requires authorized mapping, `shared` requires publisher capability | Old and new scopes must both be authorized; scope changes require publish/manage capability | Add explicit scope kind and creator; department-scoped source must have at least one mapping before ready/commit |
| `source_departments` | Mapping visible only when parent source is visible | Department must be in effective set and parent writable; shared source has no mappings | Same checks; deletion cannot silently convert parent to shared | Deferred consistency check or atomic repository operation prevents zero-mapping department source |
| `chunks` | Shared or department-array overlap; predicate remains indexable | Ingestion principal can write only for an accessible source; chunk scope must exactly mirror source scope | Same mirror/access check; no arbitrary scope edits | Trigger/constraint or hardened helper checks denormalized scope against source mappings |
| `conversations` | Owner only; shared-link resolution uses a narrow read-only resolver, not broad runtime visibility | `employee_id` equals current user | Owner only; sharing-token lifecycle remains application-authorized | Existing owner column; consider FK from Employee |
| `conversation_messages`, `memory_blocks` | EXISTS authoritative session owner == current user | Session owner must match current user/service delegation | Same owner condition | Add FK/ownership anchor; orphan rows deny until backfilled |
| `agent_runs` | `employee_id` equals current user or explicitly delegated worker capability | Employee/principal and session owner agree | Same scope plus run-state application rules | Add/check session-owner relationship; current `employee_id` is available |
| `archival_passages` | Owner OR department overlap; shared only if explicitly represented | Owner must match or every department authorized; shared publisher required | Same scope | Replace empty-array ambiguity with explicit scope kind |
| `drafts` | Shared only if intentionally allowed; otherwise own department or DB-derived all-scope permission | Department required for normal financial draft; shared/global financial creation requires explicit exceptional capability | Old/new scope authorized; RLS limits row transition | Migrate NULL rows explicitly; app still enforces maker-checker, status, payload, export |
| `audit_log`, `tool_call_attempts` | No normal runtime SELECT; diagnostics/security views or controlled roles only | Actor equals context actor; required request/resource linkage; runtime append only | Runtime UPDATE/DELETE denied | Add structured resource/scope columns if user-facing audit needs row isolation; JSON detail alone is insufficient |
| Private/runtime upload metadata | Same policy as its Source/owner metadata | Scope must be explicit and authorized | Same | File bytes remain outside PostgreSQL and require separate access control |

Every protected table is `ENABLE ROW LEVEL SECURITY` plus `FORCE ROW LEVEL SECURITY`. Runtime grants are necessary but not sufficient; both `USING` and `WITH CHECK` are defined per operation. PostgreSQL policy never substitutes for `BRV-BIZ-002` object predicate, maker-checker, voucher state, approved-only export, or journal validation.

## Rollout plan

### Phase 0 — Direct application remediation (immediate, independent)

- Implement all seven T10 pilot-blocker packages and their regression tests, including `BRV-BIZ-002` scoped approve/reject.
- Add the direct `BRV-DATA-002` session ownership guard/test without changing its evidence verdict.
- Do not wait for DBISO schema, roles, or policies.

### Phase 1 — Normalize contract and restrict roles

1. Run read-only deployed-role/grant/owner inventory and legacy scope/session-owner counts.
2. Add explicit scope/creator/owner fields as nullable compatibility columns; add service-principal/capability tables only for observed worker/scheduled needs.
3. Backfill only rows with verified ownership/classification; quarantine ambiguous NULL/empty rows.
4. Deploy dual-write/context-capable code while application predicates remain authoritative; remove service-owned commits progressively in favor of UoW ownership.
5. Create owner/app/MCP/worker/diagnostic/migrator roles, revoke PUBLIC/default excess grants, and prove runtime owns nothing and has no bypass.

### Phase 2 — Transaction context and shadow policies

1. Introduce context-bound AsyncSession factories/pools and per-transaction begin hook.
2. Convert MCP bootstrap and worker envelopes; require explicit service principals.
3. Create hardened helper functions and complete per-operation policies in migration scripts.
4. Exercise policies using canary/shadow runtime roles in CI/staging and production read-only probes. Compare application predicate results against RLS results; any difference blocks cutover.
5. Benchmark retrieval/vector plans, write paths, cancellation, and pool reuse. Keep production application predicates enabled.

### Phase 3 — Full enforcement and recovery proof

1. Ensure every deployed API/worker/MCP instance is context-aware; mixed old/new binaries are not allowed at credential switch.
2. Enable and FORCE RLS on protected tables; switch each execution path to its restricted credential/pool.
3. Revoke legacy owner/DBA runtime grants and remove or convert unfiltered views to security-invoker behavior.
4. Verify `pg_roles`, `information_schema.table_privileges`, `pg_policies`, `pg_class.relrowsecurity/relforcerowsecurity`, default privileges, and policy behavior.
5. Run backup/restore drill and re-verify owner, grants, helpers, policies, FORCE flags, and negative isolation tests before declaring complete.

### Compatibility, rollback, observability

- Migration order is expand -> backfill/quarantine -> dual write -> context-capable deploy -> shadow test -> FORCE enforcement -> old-grant revocation -> contract cleanup.
- Old binaries without context will see empty results/write errors under RLS; therefore FORCE/switch occurs only after fleet convergence. Database migrations remain backward-compatible until that point.
- Rollback removes FORCE/enforcement through the migrator and returns to restricted roles plus application predicates; it never gives runtime owner/DBA credentials. Normalized scope data and direct T10 fixes remain.
- Context binding logs principal kind/ID hash or non-sensitive identifier, request/job ID, auth source, DB role, and transaction outcome. Do not log data content, tokens, or department lists unnecessarily.
- Monitor missing-context events, RLS write-check violations, MCP/worker denials, policy-vs-application shadow mismatches, transaction duration, pool checkout time, query plans, p95 latency, and retrieval recall.

## Required tests

| # | Test | Required assertion |
|---:|---|---|
| 1 | Pooled request A/B | Force department A then B through the same physical pooled connection; B cannot see A and context reports only B inside its transaction. |
| 2 | Exception/rollback/cancellation | Raise before commit, explicit rollback, and cancel an async task; returned connection has no effective prior context and the next principal remains isolated. |
| 3 | Scoped SELECT | Own/shared rows are visible; foreign department and foreign owner rows are absent through base table, ORM, view, vector, and lexical paths. |
| 4 | Scoped INSERT | User can insert authorized department/owner rows; foreign, missing-scope, and implicit shared/global inserts fail at DB even when application predicate is omitted. |
| 5 | Scoped UPDATE/DELETE | User cannot mutate/delete a foreign row or change an own row to foreign/shared scope; row count and audit remain unchanged. |
| 6 | Shared publisher | Scoped user cannot create/convert to shared; DB-derived privileged publisher succeeds; revoking capability takes effect on the next transaction/job. |
| 7 | Agent session | User B cannot read/write User A's conversation, messages, memory blocks, archival owner data, or AgentRun; orphan session rows fail closed. This complements, not confirms, `BRV-DATA-002`. |
| 8 | MCP | Valid token sees only its current owner/department/shared scope; revoked/invalid token and bootstrap failure perform no protected read; MCP role cannot write. |
| 9 | Worker | Job without principal/capability, with revoked principal, or with inaccessible source fails closed; scoped ingestion cannot write chunks with broader scope than source. |
| 10 | Migration/runtime role | Migrator can apply/rollback policy DDL; runtime roles are NOSUPERUSER/NOBYPASSRLS, own no protected objects, cannot disable RLS, and cannot assume owner/break-glass. |
| 11 | Restore | Restored target preserves/recreates correct owners, grants, default privileges, helper ownership/search path, policies, ENABLE/FORCE flags, and passes negative tests before traffic. |
| 12 | Financial transition | Pre-fix foreign approve/reject test fails against application service; after direct `BRV-BIZ-002` fix it passes with and without RLS. RLS is not accepted as the only fix. |
| 13 | Multi-commit compatibility | One AsyncSession performs commit then a second transaction; begin hook reapplies the same principal and never runs a protected statement without context. |
| 14 | Nested transaction | SAVEPOINT success/rollback preserves the outer principal; attempts to rebind/elevate context fail. |
| 15 | Streaming/agent lifetime | No transaction remains open during simulated slow LLM/SSE wait; later writes open a fresh transaction with the same principal. |
| 16 | Security-definer hardening | PUBLIC cannot execute helpers; malicious `search_path`, invalid UUID/context, and direct function arguments cannot expand scope. |
| 17 | Policy parity | For a seeded identity matrix, application predicate results equal RLS results for reads and allowed writes; mismatch blocks enforcement. |
| 18 | Performance/recall | Representative vector/lexical/source/draft queries preserve intended indexes and retrieval recall; p95 regression follows ADR thresholds. |

## T12 database-isolation packages

| Package ID | Goal | Scope | Dependencies | Required tests | Rollback | Effort |
|---|---|---|---|---|---|---|
| DBISO-01 | Normalize identity/scope contract | Explicit scope kinds; creator/owner/session anchors; legacy NULL/empty inventory, backfill/quarantine; service-principal schema only where needed | T10 direct fixes remain parallel; deployed data inventory | #3–7, #12, #17 | Keep additive columns, disable dual-write, no ambiguous row promoted to shared | L |
| DBISO-02 | Restrict runtime database roles | Owner/app/MCP/worker/migrator/diagnostic/backup/break-glass roles; grants/default privileges; remove trusted claim from unfiltered views | Deployed role inventory; DBISO-01 table/action needs | #8–12, role catalog assertions | Restore prior restricted grants only; never runtime owner/DBA | M |
| DBISO-03 | Add transaction-local principal context | Context-bound AsyncSession/UoW; per-transaction begin hook; immutable session context; cancellation/streaming/pool handling | DBISO-01 principal contract | #1–2, #13–16 | Feature-disable context binding while policies remain shadow/disabled | M |
| DBISO-04 | Add RLS policies and write checks | Hardened helpers; SELECT/INSERT/UPDATE/DELETE policies; ENABLE/FORCE RLS; scope mirror constraints; audit append rules | DBISO-01, DBISO-02, DBISO-03; policy parity and perf baseline | #3–7, #10, #12, #16–18 | Disable/NO FORCE policies via migrator; retain roles, schema, predicates | XL |
| DBISO-05 | Cover MCP and worker principals | MCP bootstrap resolver/read pool; principal-aware job envelopes; registered service principals/capabilities; ingestion scope checks | DBISO-01, DBISO-03; complete scheduled/job inventory | #8–9, #13, #15–16 | Revert to synchronous/user path or disable jobs/MCP; never fall back global | M |
| DBISO-06 | Restore and policy verification | Catalog verifier, deployment preflight, backup/restore runbook and drill, break-glass audit, enforcement cutover checks | DBISO-02, DBISO-04, DBISO-05 | #10–11, full isolation suite | Keep traffic off restored target or revert enforcement to restricted predicates | M |

These six packages contain only database-isolation work. They do not repeat or gate the seven T10 pilot-blocker packages.

## Explicit non-decisions

- T11 does **not** delay `BRV-BIZ-002`; scoped approve/reject remains an immediate application fix with its own regression test.
- RLS is **not** maker-checker and does not decide approver identity, self-approval, approval order, or voucher state.
- RLS is **not** journal/payload/number validation and does not make an accounting proposal correct.
- T11 does not decide or introduce a knowledge graph.
- T11 does not decide planner/executor/verifier or multi-agent architecture.
- T11 does not propose microservices.
- T11 does not restructure the repository.
- T11 does not redesign the seven T10 pilot blockers or any target architecture outside database isolation.
- No production code, configuration, migration, or test was modified in T11; only this artifact was created.

## Open evidence gaps

| Evidence state | Missing evidence | Exact evidence needed | Effect |
|---|---|---|---|
| NEED FILE/CONTEXT | Deployed role/grant/ownership state | `SELECT version()`; `\du+`; role attributes; table/schema/default privileges; owners; `pg_policies`; `relrowsecurity/relforcerowsecurity`; current app/MCP/worker login names | Blocks DBISO-02 design finalization and enforcement cutover, not the D decision. |
| NEED FILE/CONTEXT | Legacy shared/private classification | Counts and approved classification of sources with no mappings, empty-scope chunks/archival rows, NULL drafts, and their creators/departments | Blocks DBISO-01 backfill and shared-policy enablement. |
| NEED FILE/CONTEXT | Session ownership completeness | Counts of conversations, messages, blocks, AgentRuns, and orphan/mismatched session IDs; evidence whether every agent session should map to a Conversation | Blocks owner-policy enablement for memory/run tables; does not validate `BRV-DATA-002`. |
| NEED FILE/CONTEXT | External scheduled/support job inventory | Job definitions, initiators, required tables/actions/departments, queue trust boundary, and revocation behavior | Blocks service-principal grants for those jobs; unknown jobs receive no access by default. |
| NEED FILE/CONTEXT | Deployed PostgreSQL/version/plan baseline | Actual PostgreSQL version, representative row counts/distributions, vector/search plans, latency/recall baseline | Blocks use of version-specific security-invoker view behavior and Phase 3 performance approval. |
| NEED FILE/CONTEXT | Backup/restore execution | Current backup credential, dump flags, target ownership behavior, restore command, and completed drill evidence | Blocks DBISO-06 completion and Phase 3 operational sign-off. |
