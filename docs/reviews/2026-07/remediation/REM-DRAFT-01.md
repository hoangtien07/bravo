# REM-DRAFT-01 — Mandatory draft department owner

Status: Complete

## Failure reproduced

Generic/AP/agent creation could persist a draft with `department_id=NULL`; existing read predicates interpret that as shared/global.

## Change

- `app/erp/draft_queue.py:resolve_draft_department` treats a client-requested department as a request only and accepts it only when it is authorized by the principal.
- `create_draft` now resolves a required authoritative department before hashing, persistence, or audit writes. Ambiguous, foreign, invalid, and omitted ownership paths fail closed.
- Financial journal proposals are normalized through the shared validator before persistence.

## Tests

`python -m pytest -q tests/test_draft_queue.py tests/test_draft_leak_probe.py tests/test_draft_scope_remediation.py tests/test_journal.py tests/test_journal_export.py tests/test_ap_service.py` — 33 passed.

The focused test proves no fake DB write occurs for zero/multiple/foreign scope and that a single authoritative department is persisted.

## Compatibility and rollback

No migration or config change. Existing one-department creators remain compatible. Callers with ambiguous identity must send an authorized explicit owner or be rejected; no implicit global fallback remains. Rolling back this guard would re-open the pilot blocker.

## Remaining risk

PostgreSQL integration execution remains pending CI/staging because the local database connection is unavailable.
