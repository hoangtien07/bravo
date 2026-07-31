# WP-03 — Bank deterministic engine status

Status: `IMPLEMENTED — HELD-OUT EVIDENCE PENDING`
Recorded: 2026-07-31
Baseline commit: `894c77de5b1e6757949a3336d44ef8f96399c492`

## Delivered

- Typed, bounded, deterministic Bank statement ↔ BRAVO bank-ledger engine.
- Exact, tolerance, aggregation, duplicate, unmatched and ambiguous result classes with frozen
  reason codes, policy ID and decimal semantics.
- Stable input ordering, duplicate-ID rejection and approved input-size limits.
- No LLM/model/runtime dependency or call path.

## Verification

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_core_v2_wp01_schema.py tests/test_core_v2_wp01_review.py tests/test_core_v2_case_state.py tests/test_core_v2_bank_engine.py
```

Result: `24 passed` (2026-07-31), including 100% exact match against every public frozen golden
result and a permutation/determinism assertion. Ruff passed for the same source/test scope.

## Evidence limit

The sealed held-out payload is intentionally absent from the implementation worktree. Therefore
the repository cannot yet claim “zero critical false negatives on held-out critical cases.” The
evaluator must run the same engine against the sealed pack and retain its independent result before
WP-03 can be declared fully passed. This is separate from the owner-approved waiver of individual
SME signing steps.

## Next dependency gate

Do not treat WP-04/API/export or a quality/release claim as proven until the evaluator-held-out
result is supplied. The deterministic engine remains available for evaluator execution without an
LLM or BRAVO connector.
