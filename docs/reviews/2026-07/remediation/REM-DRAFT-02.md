# REM-DRAFT-02 — Scoped approve/reject transitions

Status: Complete

## Failure reproduced

`approve_draft` and `reject_draft` loaded a known UUID via `db.get` without an object-scope predicate. Maker-checker, hash, and advisory locking did not compensate for cross-department transition authority.

## Change

- `app/erp/draft_queue.py:approve_draft` and `reject_draft` now load `Draft.id` through `draft_scope_filter(identity)` before changing state.
- Existing advisory lock, pending-state, maker-checker, hash, and audit controls remain in place.

## Tests

- Pure draft regression suite: 38 passed, 1 PostgreSQL test skipped locally.
- `tests/test_draft_authorization_integration.py` adds the DB-backed A/B approve/reject matrix; it is skipped only when PostgreSQL is unavailable.

## Compatibility and rollback

No migration/config change. Scoped actors receive the existing non-enumerating transition failure for a foreign UUID. All-scope behavior remains explicit through the existing predicate. Do not roll back without disabling financial approval.

## Remaining risk

The integration assertion must run in CI/staging with migrations and seeded test employees before pilot completion.
