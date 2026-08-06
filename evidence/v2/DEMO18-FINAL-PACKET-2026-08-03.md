# Plan 18 final internal-demo evidence packet

Status: `TECHNICAL DEMO-COMPLETE — FigmaMake V2 local synthetic internal demo ready for owner evaluation`

Date: 2026-08-03

## Exact bounded claim

`FigmaMake_UI/` is a locally runnable, synthetic-only internal demo of BRAVO Accounting
Intelligence. Normal navigation exposes live Knowledge Chat and authorized Accounting Operations;
the latter completes Bank Reconciliation, Voucher Evidence & Accounting Review, and Period Close
Readiness through maker → independent reviewer → non-executing artifact export. This is not a
claim of conversational quality, SME correctness, customer-data permission, pilot eligibility,
ERP execution, recovery/deployment readiness or production readiness.

## Evidence index

| Area | Evidence |
|---|---|
| Baseline/runtime | [DEMO18-00 baseline](DEMO18-00-BASELINE-2026-08-03.md) |
| Chat contract/SSE | [DEMO18-02 live Chat](DEMO18-02-LIVE-CHAT-SSE-2026-08-03.md), [Knowledge Chat API contract](../../contracts/KNOWLEDGE-CHAT-API-V1.md) |
| Three cases/negative controls | [DEMO18-05/06 lifecycle](DEMO18-05-06-LIVE-THREE-CASE-2026-08-03.md) |
| Identity/authorization | [DEMO18-06 identity](DEMO18-06-IDENTITY-AND-SECONDARY-CASE-2026-08-03.md), [ownership probe](../../scripts/demo18_ownership_probe.py) |
| Browser/a11y/responsive | [DEMO18-08 browser](DEMO18-08-LIVE-BROWSER-2026-08-03.md), [live Playwright test](../../FigmaMake_UI/e2e/live-demo.pw.ts) |
| Launcher/reset/rollback/hashes | [DEMO18-09 packaging](DEMO18-09-PACKAGING-2026-08-03.md), [local runbook](../../docs/RUNBOOK-DEMO18-LOCAL-SYNTHETIC.md) |
| Technical rehearsal | [DEMO18-09 rehearsal](DEMO18-09-TECHNICAL-REHEARSAL-2026-08-03.md) |
| Owner decision (pending) | [owner evaluation record template](DEMO18-OWNER-EVALUATION-RECORD-TEMPLATE.md) |

## Route and API boundary

| Normal route | Server-owned source | Boundary |
|---|---|---|
| `/login` | auth config/login/me | local password-login demo path |
| `/`, `/c/:id`, `/conversations` | conversation CRUD and authenticated POST-SSE | live; `fixture:*` IDs rejected |
| `/shared/:token` | public read-only shared conversation endpoint | no owner controls exposed |
| `/work`, `/work/new/:type`, `/work/cases/:id` | AccountingCase V2 API | server capability/state/revision controls remain authoritative |

The normal product shell links only Knowledge Chat, recent conversations and authorized
Accounting Work. Legacy/prototype paths remain outside normal navigation under their explicit QA
boundary; no request interception is used in the live suite.

## Identity and invariant matrix

| Synthetic identity | Server capability | Demonstrated boundary |
|---|---|---|
| maker | own-department read/create | creates, adds evidence and runs checks; self-review rejected |
| reviewer | own-department read/review | reviews and exports the current revision |
| outside department | no AccountingCase capability | cannot enumerate/read ownership-probe conversation, attachment or source |

All identities are non-admin. No credential, token, content identifier or customer data is retained
in this packet. Direct lifecycle evidence confirms stale revision rejection and
`artifact_produced_not_executed` for every case.

## Final gate results

- Candidate: typecheck; `22` Vitest tests across `7` files; axe gate; production build — pass.
- Live browser: `2` tests — pass in `24.7s`; actual local password login, Chat SSE/durable reload,
  attachment/citation/feedback/share and isolated three-case maker/reviewer flows.
- Accessibility: zero critical axe WCAG 2 A/AA violations on sign-in, Chat, share and exported
  case workspaces; mobile drawer Escape/focus-return verified.
- Responsive: no horizontal overflow at 1440×900, 1024×768, 768×1024 and 390×844 in light/dark.
  Final screenshots are `DEMO18-chat-{viewport}-{light|dark}.png` beside this packet.
- Candidate bundle tree SHA-256: `3fe11615ee477bc8ef285eed16459bb953c0ea31dbda272e344b23695fdad648`.
- Classic comparator bundle tree SHA-256: `9ba471537adfa747a76f4e1be625b25f20d9a29c0dfb02af2ce427256e64c1fa`.

## Known limitations and deferred gates

- The local runtime can surface tool-style Chat content; no conversational-quality claim is made.
- The visual/browser evidence uses synthetic data only; no real customer/ERP data is authorized.
- Owner evaluation is pending; the automated technical rehearsal is not owner acceptance.
- Blind SME review, frozen A/B/C/D conversation-quality evidence, pilot guardrails, operator
  recovery/deployment and production evidence remain separately governed by Plans 10, 12 and 15
  and ADR-0032/0033.

## Rollback

Stop the FigmaMake local presenter and use the untouched `frontend-react/` comparator per the
local runbook. Do not copy sessions, fixture state or source data between frontends. Production
and static cutover remain disabled.
