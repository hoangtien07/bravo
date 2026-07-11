# T2 — Tenant/RLS/Database/Memory Schema

Scope read: T0/T1 artifacts; `app/database/**`, `alembic/**`, `app/security/rls.py`, `app/agent/memory.py`, direct session/background consumers (`app/agent/conversations.py`, selected `app/agent/loop.py` call sites, `app/worker.py`), and RLS/memory tests. No database-backed test was run: the host Python toolchain is unavailable.

## Principal → session → query trace

| Stage | Implementation evidence | Scope state / boundary |
|---|---|---|
| Authenticated principal | T1 established `get_current_identity` loads `Employee` and builds `Identity(employee_id, department_ids, permissions, is_admin)`. | Department scope is application data, not a database session variable. |
| Database session | `app/database/__init__.py:get_db` and `async_session_factory` create a normal `AsyncSession` from one `DATABASE_URL`. | No `SET LOCAL`, `SET ROLE`, `set_config`, or connection-pool tenant cleanup was found in the scoped database/migration paths. |
| Knowledge read scope | `security.rls.chunk_scope_filter` / `source_scope_filter` generate application-side SQL predicates from `Identity`; API and retriever call sites pass the identity. | Read filtering depends on each query applying the predicate. T3 verifies source→chunk propagation. |
| Conversation scope | `conversation_scope_filter` uses `Conversation.employee_id`; `conversations.ensure_conversation` checks owner for the streaming route. | Message/core-memory schema stores only `session_id`; T4 verifies all agent entry paths. |
| Archival-memory scope | `MemoryStore._archival_scope` uses `owner_id` or explicit department overlap; `archival_search` places it in the SQL `WHERE`. | App-level predicate, not PostgreSQL native RLS. |
| Background ingestion | `worker.ingest_task(ctx, source_id, path)` opens `async_session_factory` and calls `ingest_source` without an `Identity` argument. | T3 must verify that source-derived scope, rather than caller context, is persisted to chunks. |

## Migration and DB-role evidence

- `0001_init` creates the schema and indexes for department arrays; it does not create PostgreSQL row-security policies.
- Across the migration chain, no `CREATE POLICY` or `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` statement was found.
- `0004_db_roles` creates `bravo_agent` and grants it `SELECT` on `app_safe.v_chunks_scoped` and `v_archival_scoped`, but both views are literal `SELECT *` over their base tables.
- The application session factory queries ORM base tables and has no role switch or separate read/write pool. Actual database grants and the deployed login role remain `NEED FILE/CONTEXT`.

## Data classification and lifecycle

| Data type | Current store | Scope enforcement | Provenance | Retention/deletion | Assessment |
|---|---|---|---|---|---|
| Identity / department membership | `employees`, `departments`, `employee_departments` | `Identity` is built from `Employee.departments`; route dependencies consume it | Employee ID and permission array | No retention/delete workflow in scoped code | VERIFIED schema→principal mapping |
| Approved knowledge source | `sources`, `source_departments` | `source_scope_filter` applies department relation at read time | Filename, knowledge type, created time | No source lifecycle/deletion reviewed here | VERIFIED read predicate; T3 owns ingestion lifecycle |
| Knowledge chunk | `chunks` | `chunk_scope_filter` applies denormalized `department_ids` in query | Source ID, page/sheet/cell/heading fields | No tombstone/reindex lifecycle reviewed here | VERIFIED schema; T3 verifies source-scope propagation |
| Conversation metadata | `conversations` | Owner predicate on `employee_id` in API conversation flow | Owner, timestamps, optional shared token | T1 route deletes the conversation; no DB foreign-key cascade observed | VERIFIED owner field; T4 checks all session entry paths |
| Recall memory | `conversation_messages` | `MemoryStore.recall_recent` filters only by `session_id` | `trust_level`, optional `source`, created time | Conversation delete route deletes messages; no FK to `conversations` in model/migration | VERIFIED; see BRV-DATA-002/003 |
| Core memory / preferences | `memory_blocks` | `MemoryStore._block` filters only by `session_id` | Label/value only | Conversation delete route deletes blocks; no timestamp, owner column, or retention field | VERIFIED for core memory; no separate preference store found |
| Archival memory | `archival_passages` | `_archival_scope`: owner or explicit department overlap; admin/`doc:read:all` bypass | `trust_level`, optional `source`, tags | No production deletion call or timestamp field found in scoped paths | VERIFIED; see BRV-DATA-004 |
| Agent/draft state | `agent_runs`, `drafts`, `tool_call_attempts`, `audit_log` | Application/service predicates; draft department may be nullable | Checkpoint JSON, hashes, actor/run IDs | No retention policy found in scoped models/migrations | T4/T5 review business state; not ERP system-of-record evidence |
| Organization/site config | No ORM model found; T0 maps environment/YAML paths | No request-scoped tenant field found | NEED FILE/CONTEXT | NEED FILE/CONTEXT | Configuration/provisioning boundary belongs to T6 |
| Support case | No matching ORM model found in scoped schema | NEED FILE/CONTEXT | NEED FILE/CONTEXT | NEED FILE/CONTEXT | Not inferred from file names |

## Findings

| ID | Severity tạm thời | Evidence state | File:symbol | Evidence ngắn | Consumer/impact | Next action | Needs Sol review |
|---|---|---|---|---|---|---|---|
| BRV-DATA-001 | High | VERIFIED | `alembic/versions/0004_db_roles.py:upgrade`; `app/database/__init__.py:async_session_factory` | Migration grants `bravo_agent` access to two views defined as unfiltered `SELECT *`; no native row-security policy is created in the migration chain. The app uses one base-table ORM session factory and contains no role/session-context switch. | Department isolation has no database-enforced backstop when an application query omits its predicate; whether the granted role is provisioned at runtime is unknown. | Verify deployed grants/login role and decide the required independent database enforcement with Sol; add migration-level policy/privilege tests after the decision. | Yes |
| BRV-API-002 | High | VERIFIED | `app/api/routes_sources.py:upload_source`; `app/database/models.py:SourceDepartment`; `app/security/rls.py:source_scope_filter` | Caller form IDs are inserted as `SourceDepartment` rows; schema only requires a valid department FK, not membership in the caller's departments. The source read predicate uses those rows directly. | T1's conditional write-scope concern is confirmed for source write and source read paths: a reachable scoped writer can assign a source to another existing department or make it global. Chunk propagation remains T3 scope. | Keep ID from T1. T3 verify chunk propagation; Sol verify severity/remediation because this crosses private/shared and RLS boundaries. | Yes |
| BRV-DATA-002 | High | INFERRED | `app/api/routes_agent.py:agent_ask`; `app/agent/loop.py:AgentSession.__init__`; `app/agent/memory.py:recall_recent` | `/agent/ask` passes caller-supplied `session_id` into `AgentSession` without the owner check used by the streaming conversation route. Recall/core-memory queries filter only by that session ID; their schema has no owner/FK constraint. | A caller who knows another session UUID may load that session's history into the agent context. Direct response disclosure needs T4 confirmation, but the cross-user context read path exists. | T4 trace the complete agent response/tool path and add an ownership test for `/agent/ask`; evaluate schema constraints during remediation design. | Yes |
| BRV-DATA-003 | High | VERIFIED | `app/agent/memory.py:history_for_prompt`; `app/agent/loop.py:_summarize` | For older turns, `history_for_prompt` concatenates raw `m.content` (without `frame_by_trust`) and sends it to `_summarize`; the returned summary is stored in a core block and later emitted as a system message. | An untrusted document/tool/ERP turn can bypass the normal DATA framing during history compression and influence persistent prompt context. | T4 verify model/tool authority impact and add a long-history untrusted-content test; Sol must decide the required trusted-summary boundary. | Yes |
| BRV-DATA-004 | Medium | VERIFIED | `app/database/models.py:MemoryBlock`; `ArchivalPassage`; `app/agent/memory.py:MemoryStore` | Core blocks and archival passages lack a retention timestamp/policy field; `MemoryStore` has insert/read methods but no production deletion path. The conversation delete route covers messages/blocks, not archival passages. | Long-term or private-derived memory can remain without a scoped lifecycle or deletion mechanism. | Define retention/deletion requirements and test cascade/erase behavior; T6 supplies deployment/backup context. | No |

## Test evidence and command

| Evidence | State | Notes |
|---|---|---|
| `tests/test_rls.py` exercises deny/default, global, own-department and all-scope logic. | Read only; not executed | Does not exercise PostgreSQL policies or source writes. |
| `tests/test_memory_rls.py` exercises archival SQL predicate shape, owner/department retrieval, session recall, and untrusted framing. | Read only; not executed | Does not cover `/agent/ask` session ownership, history summarization, retention, or DB roles/views. |
| `tests/test_draft_leak_probe.py` exercises draft department helper behavior. | Read only; not executed | T5 owns draft state enforcement. |
| Expected scoped command | `pytest -q tests/test_rls.py tests/test_memory_rls.py tests/test_draft_leak_probe.py` | Not run: host Python/pytest unavailable per T0. |

## Bypass and deployment evidence still needed

| Area | State | Needed evidence / handoff |
|---|---|---|
| Deployed DB role, grants, superuser/BYPASSRLS attributes, and actual policies | NEED FILE/CONTEXT | T6/deployment environment or a non-destructive database privilege inspection |
| Connection-pool transaction cleanup for tenant context | VERIFIED no context-setting code found; runtime privilege behavior is NEED FILE/CONTEXT | Covered by BRV-DATA-001 and T6 provisioning review |
| Worker source→chunk scope | NEED FILE/CONTEXT | T3 inspect `ingest_source` and chunk creation |
| Direct agent session response leakage | NEED FILE/CONTEXT | T4 complete `AgentSession` trace and test path |
| ERP state and approval mutation | NEED FILE/CONTEXT | T5 scope |

## T2 exit check

- Schema → session → query trace: complete from `Identity` through `AsyncSession`, application predicates, memory queries, and worker entry.
- BRV-API-002: **Confirmed** for source write and source read; chunk propagation is explicitly handed to T3.
- Conversation/recall/core/archival memory, knowledge, configuration, draft state, and unsupported support-case categories are separated above.
- Bypass paths and deployment evidence gaps are recorded; no production code, config, migration, or test was changed.
