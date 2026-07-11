# REM-EXPORT-01 — Approved-only financial export

Status: Complete

## Failure reproduced

Individual and batch journal export checked kind/scope but not `Draft.status`, so pending or rejected drafts could produce a manual ERP-import artifact.

## Change

- `app/api/routes_drafts.py:export_draft` and `export_batch` require every requested journal to be approved and reject mixed/partial batches.
- Both paths revalidate the journal payload immediately before rendering.
- `frontend-react/src/features/chat/DraftCard.tsx`, `features/drafts/DraftsQueuePage.tsx`, and `features/money/MoneyEnginePage.tsx` show/enable export selection only for approved journal drafts. The backend remains the enforcing control.

## Tests

`python -m pytest -q tests/test_draft_export_gate.py …` — 38 passed, 1 DB test skipped; the export matrix covers pending, rejected, approved, mixed batch, and invalid approved stored payload.

Frontend type-check was not run locally because `frontend-react/node_modules` is absent. It must run in CI with the pinned frontend dependencies.

## Compatibility and rollback

No migration/config impact. Approved CSV/XLSX remains supported; pending/rejected/mixed requests now return a stable conflict. Do not restore pre-approval export behavior.

## Remaining risk

The UI is an affordance only. CI must exercise the direct API status matrix and frontend typecheck before pilot sign-off.
