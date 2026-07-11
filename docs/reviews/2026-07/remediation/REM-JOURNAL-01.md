# REM-JOURNAL-01 — Journal payload integrity at every boundary

Status: Complete

## Failure reproduced

The generic draft endpoint accepted arbitrary JSON as `journal_entry`; approval only checked hash and export rendered the payload without strict journal validation.

## Change

- `app/api/routes_drafts.py:DraftIn` allowlists the generic endpoint to `journal_entry`.
- `app/erp/draft_queue.py:validate_draft_payload` validates at create and revalidates before approval.
- `app/accounting/journal.py:JournalEntryPayload` rejects an unknown chart-of-accounts code as well as existing balancing invariants.
- Export revalidates rather than trusting stored JSON.

## Tests

`python -m pytest -q tests/test_draft_export_gate.py tests/test_draft_scope_remediation.py tests/test_journal.py tests/test_journal_export.py tests/test_ap_service.py` — included in the 38-pass focused suite; malformed and unknown-account payloads are denied.

## Compatibility and rollback

Deterministic XML/AP and agent journal paths continue to use `JournalEntryPayload`. No migration/config change. Non-journal generic draft creation is no longer an accepted public generic-route contract; direct typed paths remain separate.

## Remaining risk

This is a payload/integrity gate, not accounting semantic approval, maker-checker, or ERP posting validation.
