# DEMO18-09 technical rehearsal

Status: `PASS — repeatable local synthetic technical rehearsal; owner evaluation pending`

Date: 2026-08-03

## Run

The local API was started with the explicit synthetic AccountingCase overlay and seeded with the
non-admin maker and reviewer identities. The credential-free source test and its short-lived
runner completed in `24.7s`:

```text
ok maker completes live Chat, durable reload, and read-only share
ok maker and independent reviewer complete all three browser case lifecycles
2 passed
```

## Script coverage

| Demo-script section | Technical rehearsal evidence |
|---|---|
| 1–3 | Password login, live POST-SSE Chat, durable reload, synthetic attachment, returned citation, feedback and read-only share |
| 4–7 | Maker creates/evidences/checks Bank, Voucher and Period; isolated reviewer reloads/reviews/exports each |
| 8 | Direct API probe verifies stale revision rejection and maker self-review denial for every case |
| 9 | Synthetic-only overlay and `artifact_produced_not_executed` assertion remain visible in evidence |

The run additionally checks axe critical violations, responsive non-overflow at four viewports,
mobile drawer Escape/focus return, and the final light/dark screenshot matrix.

## Deliberate limitation

This compressed automated rehearsal does not substitute for the 12–15 minute owner-led review.
No owner acceptance/rejection was observed or inferred. The next human action is to run the script
in Plan 18 section 8 with the owner and record their decision separately.
