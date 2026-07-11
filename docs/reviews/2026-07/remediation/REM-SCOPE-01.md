# REM-SCOPE-01 — Source write scope authorization

## Status

Implemented application-level remediation for `BRV-API-002`. No PostgreSQL RLS, migration, production-data operation, ingestion-classification change, or rerank change is included.

## Failure reproduced

- Prior evidence state: **VERIFIED** in T10. `routes_sources.upload_source` accepted omitted/empty or caller-supplied `department_ids`, then inserted mappings directly; empty input persisted no mapping and was therefore global/shared in the existing read/retrieval model.
- Regression reproduction: `tests/test_source_write_scope.py` captures the prior unsafe cases: omitted/empty scope, foreign scope, mixed A+B scope, and unprivileged shared publication. The pre-fix route would not satisfy these assertions.
- Runtime note: the original vulnerable code was not restored/re-executed. The new database-backed HTTP + lexical-retrieval test is present but skipped locally because PostgreSQL/Docker is unavailable. This is not counted as runtime proof.

## Files changed

| File | Change |
|---|---|
| `app/security/rls.py` | Added `source_create_scope_level` and `resolve_source_write_scope`: `doc:create:all` is the explicit all-scope/shared-publication capability; `doc:create:own_dept` is constrained to authoritative department membership. |
| `app/api/routes_sources.py` | Parses client scope as a request, resolves it before any database/file write, adds explicit multipart `shared` flag, and returns stable 403/422 scope errors. |
| `tests/test_source_write_scope.py` | Added pure scope-policy, pre-persistence route, and DB-backed upload-to-lexical-retrieval isolation coverage. |

`app/security/auth.py`, `app/api/routes_admin.py`, and `scripts/seed.py` were reviewed but not changed: `doc:create:all` is already assignable and the seeded admin already holds it. The unrelated legacy bare `doc:create` vocabulary issue is not changed by this package.

## Permission contract

| Principal/request | Before | After |
|---|---|---|
| `doc:create:own_dept` + own department | Accepted only because the route trusted client IDs. | Allowed when all requested IDs are in the authenticated identity's departments. |
| `doc:create:own_dept` + omitted/empty scope, one department | Created a no-mapping global source. | Server resolves to the sole authoritative department; source is not global. |
| `doc:create:own_dept` + omitted/empty scope, zero/multiple departments | Created a no-mapping global source. | Stable 422; no Source, SourceDepartment, Chunk, or upload file is created. |
| `doc:create:own_dept` + foreign or mixed A+B scope | Created caller-selected mapping(s). | Stable 403; no persistence. |
| `doc:create:own_dept` + `shared=true` | No explicit shared signal existed; empty mapping could be global. | Stable 403. |
| `doc:create:all` + `shared=true` and no department IDs | Empty mapping could be created implicitly. | Allowed as the explicit shared-publication path. |
| `doc:create:all` + omitted/empty scope without `shared=true` | Could create an implicit global source. | Stable 422; shared publication must be explicit. |
| `is_admin` without `doc:create:all` | Generic route dependency could admit admin. | Cannot create shared/foreign source: explicit publication capability is required. |

The stored empty mapping remains the legacy shared representation until DBISO-01; this package ensures it is never produced by an omitted/empty scoped-writer request.

## Tests

| Command | Result | Coverage |
|---|---|---|
| `.venv\\Scripts\\python.exe -m pytest -q tests/test_source_write_scope.py tests/test_rls.py` | **14 passed, 1 skipped** | Own/foreign/mixed/shared policy, pre-write denial, existing read-predicate behavior. |
| `.venv\\Scripts\\python.exe -c "import app.api.routes_sources"` | Pass | Route/module import after change. |
| Bundled Python `-m py_compile app/api/routes_sources.py app/security/rls.py tests/test_source_write_scope.py` | Pass | Syntax compilation. |

The skipped test is `test_source_upload_scope_and_retrieval_isolation`. It seeds departments A/B, exercises actual multipart upload, verifies rejected requests leave no Source/Chunk, then calls `retriever.lexical_search` to prove reader B cannot retrieve A-scoped chunks but can retrieve an explicitly shared chunk. It requires a local PostgreSQL instance; Docker is unavailable in this workspace.

## Backward compatibility

- `shared` is an optional multipart field with default `false`.
- Existing single-department `doc:create:own_dept` clients that omit `department_ids` remain accepted, but are server-resolved to their one department rather than global.
- Existing zero/multi-department scoped clients must provide valid authorized department IDs; ambiguous omission now fails closed with 422.
- Existing `doc:create:all` clients must send `shared=true` to publish shared/global content. Response schema remains unchanged.

## Migration/config impact

- No schema migration, RLS policy, database role, deployment configuration, or production data change.
- No new permission string was introduced. `doc:create:all` is the explicit capability used for foreign scope and shared publication, consistent with T10/T12.

## Rollback

Revert `app/api/routes_sources.py` and the two scope helper functions together only if source uploads are disabled or the pilot is not serving scoped users. Reverting while uploads remain available reintroduces `BRV-API-002`; DBISO/RLS must not be treated as a substitute for this guard.

## Remaining risk

- **NEED FILE/CONTEXT:** Run the skipped PostgreSQL HTTP/retrieval integration test in CI or a local compose environment before claiming end-to-end runtime verification.
- This is application-layer enforcement only. DBISO-01 through DBISO-04 remain responsible for durable explicit scope semantics and independent database backstop.
- `BRV-RAG-001` remains open: trusted sensitivity classification/cloud embedding is deliberately deferred to `REM-EGRESS-01`.
- An existing multi-department frontend that omits scope receives 422 rather than global publication; client UX alignment can be handled by the subsequent source-upload package without weakening this guard.
