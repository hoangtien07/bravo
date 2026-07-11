# DBISO-EVIDENCE — Read-only database isolation fact base

Timestamp: 2026-07-10 (Asia/Saigon). No database, role, configuration, migration, or production-code change was made.

## Collection result

| Area | Evidence state | Result | Command/result |
|---|---|---|---|
| Local PostgreSQL tooling | VERIFIED | `psql`, `pg_dump`, `pg_restore`, and Docker are unavailable on this workstation. | `Get-Command …`; exit 0; each `not-found` |
| Local TCP reachability | VERIFIED | `localhost:5432` accepted a TCP probe. This does not identify the deployed database or authorize catalog access. | `Test-NetConnection localhost -Port 5432`; exit 0; `TcpTestSucceeded=True` |
| Application-DSN catalog connection | NEED FILE/CONTEXT | Read-only `asyncpg` connection using the configured application DSN (with the SQLAlchemy driver suffix removed) timed out after five seconds. No DSN or secret was printed. | `_dbiso_probe.py` temporary read-only probe; exit 1; `TimeoutError`; removed after use |
| PostgreSQL version/login role | NEED FILE/CONTEXT | Catalog query could not run. | Checklist below |
| Ownership/grants/default privileges | NEED FILE/CONTEXT | Catalog query could not run. | Checklist below |
| Superuser/BYPASSRLS/policy/FORCE RLS state | NEED FILE/CONTEXT | Catalog query could not run. | Checklist below |
| Legacy source/chunk/draft scope counts | NEED FILE/CONTEXT | Catalog query could not run. | Checklist below |
| Conversation/memory/session orphan counts | NEED FILE/CONTEXT | Catalog query could not run. | Checklist below |
| MCP/worker/scheduled-job inventory | VERIFIED (repository) | `app/mcp/server.py` and `app/worker.py` are implementation candidates; deployed process/queue inventory is not available. | T0 inventory plus current code references |
| Representative plans | NEED FILE/CONTEXT | No authenticated read-only database session. | Checklist below |
| Backup/restore command and credential model | NEED FILE/CONTEXT | Local backup tools are absent; deployed runbook/operator context was not supplied. | Checklist below |

## Operator command checklist

Run against the isolated staging/deployed database with a read-only diagnostics role. Substitute environment-managed connection variables; do not paste credentials or outputs containing secrets into this artifact.

| Evidence | Read-only command/query | Expected recorded result |
|---|---|---|
| Server/version/login role | `SELECT version(), current_database(), current_user, session_user;` | version, database, role |
| Role flags | `SELECT rolname, rolsuper, rolbypassrls, rolcanlogin FROM pg_roles ORDER BY rolname;` | runtime/migrator/admin/backup role catalog |
| Owners and RLS flags | Query `pg_class`/`pg_namespace` for `sources`, `source_departments`, `chunks`, `drafts`, `conversations`, `conversation_messages`, `archival_passages`, `agent_runs`, `audit_log`, including `relowner`, `relrowsecurity`, `relforcerowsecurity`. | owner and ENABLE/FORCE state per table |
| Grants/default privileges | Query `information_schema.role_table_grants` and `pg_default_acl`. | grants by grantee and default grants |
| Policies | `SELECT * FROM pg_policies WHERE schemaname='public' ORDER BY tablename, policyname;` | policy text/roles/commands |
| Scope legacy counts | Count sources lacking `source_departments`, chunks with `cardinality(department_ids)=0`, and drafts with `department_id IS NULL`. | counts, classified only after owner review |
| Ownership orphans | Count messages without conversation, archival rows without owner, agent runs without employee/session according to deployed schema. | counts and exact schema/version |
| Plans | `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` for representative source-mapping, lexical chunk, vector chunk, draft-scope, and session-owner queries, using non-sensitive parameters. | plan text, latency, row estimate/actual |
| Backup/restore | Provide the deployed command/runbook, credential role name, and a restore-drill result from an isolated target. | command owner, timestamp, policy/grant preservation result |

## Required operator handoff

1. A redacted read-only diagnostics connection or command output for the checklist.
2. The deployed process inventory identifying HTTP, MCP, worker, scheduler, migration, backup, and break-glass principals.
3. The backup/restore runbook and latest isolated restore-drill evidence.
4. The deployed schema/migration revision so scope/orphan queries can be matched to actual columns.

## Gate

`DBISO-01` through `DBISO-06` remain deferred. This evidence gap does not block Track A pilot-blocker remediation, but it blocks a safe DBISO rollout decision beyond ADR-DB-001.
