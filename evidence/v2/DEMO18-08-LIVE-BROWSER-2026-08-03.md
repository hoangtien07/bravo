# DEMO18-08 local API and browser evidence

Status: `RUNTIME PASS — local synthetic internal demo only`

Date: 2026-08-03

## Preconditions

- API was started through `docker-compose.demo18.yml`, which enables only the versioned synthetic AccountingCase manifest.
- API health was `ok`; runtime migration was `0020_case_v2_audit (head)`.
- The idempotent local seed created non-admin maker/reviewer identities with server-issued own-department capabilities.

## Live browser suite

The suite is [live-demo.pw.ts](../../FigmaMake_UI/e2e/live-demo.pw.ts). It has no password/token literal and no request interception. [run_demo18_live_browser.py](../../scripts/run_demo18_live_browser.py) passes the existing synthetic seed credential only to the short-lived local test process; it does not print or persist the value.

```text
Running 2 tests using 1 worker
  ok maker completes live Chat, durable reload, and read-only share
  ok maker and independent reviewer complete all three browser case lifecycles
2 passed
```

The first test uses actual password login, new-conversation POST-SSE, durable transcript reload, synthetic attachment upload/readiness, citation selection, durable feedback, and unauthenticated read-only shared transcript. The second uses isolated maker and reviewer browser contexts for Bank Reconciliation, Voucher Evidence Review, and Period Close Readiness:

```text
maker: create → attach evidence → run checks → NEEDS_REVIEW
reviewer: reload → review → export → EXPORTED
```

The server-owned browser action also validates the zero-finding review packet path used by bounded Voucher/Period cases. It does not claim model quality, blind SME review, customer-data authority, pilot eligibility, production readiness, or BRAVO execution.

The same suite injects `axe-core` in the local browser and found zero `critical` WCAG 2 A/AA
violations on sign-in, durable Chat workspace, shared transcript and each exported case workspace.
The Chat workspace was also checked at `1440×900`, `1024×768`, `768×1024`, and `390×844`; the
document had no horizontal overflow at each target viewport. At mobile size, the suite opens the
navigation drawer, closes it with Escape, and verifies focus returns to its opener.

The suite waits for the terminal SSE state (both the `Stop` control and transient “responding”
surface are absent) before producing the final visual matrix. The eight retained local-synthetic
screenshots are `DEMO18-chat-{1440x900,1024x768,768x1024,390x844}-{light,dark}.png` in this folder.
They cover the normal Chat workspace and Evidence Rail without a fixture route; representative
captures were visually inspected at 1440×900 light and 390×844 dark.

## Ownership probe

[demo18_ownership_probe.py](../../scripts/demo18_ownership_probe.py) created and then removed only
its own synthetic maker-scoped resources. It emitted no identifier, content, token or credential:

```json
{"non_owner_attachment_404":true,"non_owner_conversation_404":true,"personal_source_absent_from_outside_list":true}
```

This is direct local API proof that an outside-department identity cannot enumerate or read the
probe's conversation/attachment/source resources.
