# WP-02 — framework-independent Core V2 status

Status: `PASS — DEVELOPMENT GATE OPEN`
Recorded: 2026-07-31
Baseline commit: `0c865bf337e96144d7615eca8d24a7a5b5dabefd`
Alembic head: `0017_native_rls_backstop`

## Delivered

- Pure `AccountingCase` contracts and ports with no FastAPI, database, vector-store or model-SDK
  imports.
- Locked scope and immutable value objects.
- State-transition validation, revision/CAS protection and idempotency conflict detection.
- Evidence supersession resets evidence state and invalidates prior approval.
- Payload-bound draft approval invalidation and corrupt-state failure behavior.
- In-memory test adapter only; no API, persistence or BRAVO connector was added.

## Verification

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_core_v2_wp01_schema.py tests/test_core_v2_wp01_review.py tests/test_core_v2_case_state.py
.venv\Scripts\python.exe -m ruff check app/core_v2 tests/test_core_v2_wp01_schema.py tests/test_core_v2_wp01_review.py tests/test_core_v2_case_state.py
```

Result: `20 passed`; Ruff passed (2026-07-31).

## Next dependency gate

WP-03 may implement the deterministic Bank reconciliation engine only. It must consume the frozen
synthetic policy/fixtures, stay LLM-independent, and satisfy golden exactness plus critical-case
evidence before Bank orchestration, API or conversation work begins.
