# DEMO18-06 identity and secondary-case evidence

Status: `RUNTIME AND BROWSER PASS — local synthetic internal demo only`

## Runtime identity probe

`demo18_identity_probe.py` queried `/api/me` after password authentication without printing any
credential/token. Results:

| Identity | AccountingCase capability |
|---|---|
| maker | `read:own_dept`, `create:own_dept` |
| reviewer | `read:own_dept`, `review:own_dept` |
| outside department | none |

All three identities returned `is_admin: false`.

## Developer functional evidence

The workspace test environment ran:

```text
tests/test_core_v2_secondary_functional_http.py
tests/test_core_v2_voucher_orchestration.py
tests/test_core_v2_period_close_orchestration.py
```

Result: `4 passed, 2 skipped`. The skipped cases are not treated as a runtime pass. The suite
proves the shared-core Voucher and Period Close lifecycle at developer-test scope only.

## Live lifecycle evidence

The direct local API lifecycle proof for Bank, Voucher and Period (including stale-revision and
self-review denial) is recorded in
[DEMO18-05-06-LIVE-THREE-CASE-2026-08-03.md](DEMO18-05-06-LIVE-THREE-CASE-2026-08-03.md).

## Browser completion

The non-mocked two isolated browser-context walkthrough is now recorded in
[DEMO18-08-LIVE-BROWSER-2026-08-03.md](DEMO18-08-LIVE-BROWSER-2026-08-03.md). It exercised all three
maker → independent reviewer lifecycles without request interception. This does not elevate the
synthetic local proof into SME, pilot, customer-data or production evidence.
