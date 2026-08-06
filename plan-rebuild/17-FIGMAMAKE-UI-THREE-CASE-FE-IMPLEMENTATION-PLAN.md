# BRAVO V2 — FigmaMake UI three-case frontend implementation plan

Status: `TECHNICAL IMPLEMENTATION COMPLETE — FEV2-10 RECONCILED BY PLAN 18 LIVE EVIDENCE; OWNER EVALUATION PENDING`

Owner: project owner  
Decision date: 2026-08-02  
Candidate frontend: `FigmaMake_UI/`  
Rollback/comparator: `frontend-react/`  
Authority: ADR-0032, ADR-0033, Plan 16 and the
[FE admission decision](../evidence/v2/V2-BRAVO10-FE-ADMISSION-COUNCIL-DECISION-2026-08-02.md)

## 1. Outcome and claim boundary

Build the new Accounting Operations Hub directly in `FigmaMake_UI` and connect it to the existing
trusted FastAPI/auth/RLS shell and the durable synthetic AccountingCase V2 API.

The first delivery is one local, synthetic, three-case developer demo:

- Bank Reconciliation is the primary/deep case.
- Voucher Evidence & Accounting Review is functional/bounded.
- Period Close Readiness is functional/bounded.
- All three use one inbox, one case workspace grammar and the same evidence/review/export controls.

This plan starts Plan 16 BF-06. It does **not** mean the full V2 program is complete. Blind SME,
live-model, user-time, operator-cutover, real-data, pilot and production gates remain outside this
frontend program.

The strongest completion claim allowed by this plan is:

> Local synthetic three-case developer demo ready for human evaluation.

## 2. Verified starting state

Verified on 2026-08-02 without reading any secret value:

| Item | Current evidence | Consequence |
|---|---|---|
| Git | baseline observed at `c41255635bee7e594e4b867cf26f5691b98097cc`; remediation worktree is intentionally dirty | Preserve all existing changes; do not manufacture a clean-baseline claim |
| Alembic | `.venv` reports single head `0020_case_v2_audit` | FE DTOs target the post-BF-05 durable contract |
| Backend | admission packet records `493 passed, 35 skipped, 2 warnings` | Sufficient for FE admission; skipped/external gates remain visible |
| Candidate typecheck | `pnpm.cmd run typecheck` passes | Current TypeScript baseline is usable |
| Candidate tests | 4 files / 8 tests pass | Router/fixture/a11y smoke exists; it is not integrated contract/E2E evidence |
| Candidate build | Vite 8 production build passes; 47 modules transformed | Build baseline exists before API integration |
| Candidate runtime | React 19, React Router 7, Vite 8, Tailwind 4, Vitest | Keep this stack unless an evidenced blocker requires an ADR |
| Candidate architecture | routed prototype, QA fixtures, fixture network guard, responsive shell | Reuse the visual system and deterministic QA harness |
| Known gap | fake auth and fixture App/QA contexts still own runtime state | Replace with typed live services and session state |
| Known gap | `/accounting-work` is a static Bank frame; Voucher/Period are labelled previews | Replace with durable list/create/get/evidence/check/review/export flows |

`frontend-react` already demonstrates the repository's bearer-token login, `/api/me`, OIDC entry,
API error handling and conversation SSE behavior. It is a contract reference only. Do not copy its
visual system, change its dependencies or implement the new V2 UI there.

## 3. Product and visual direction

### 3.1 Subject, audience and single job

- **Subject:** BRAVO Accounting Intelligence, not a generic chatbot or a second ERP.
- **Primary users:** reconciliation accountant/preparer and chief-accountant/reviewer.
- **Single job:** move an AccountingCase to the next safe, evidence-backed state without confusing
  a fixture, inference, review packet or export with an executed BRAVO result.

### 3.2 Design system

Retain the approved **Assured Operations — Quản trị chắc chắn, có bằng chứng** direction:

- BRAVO Green `#00A88D` for brand/verified accents;
- Interactive Teal `#006B5D` for small controls and focus-safe interactions;
- Canvas `#F6F9F8`, Strong Text `#1F2927`, Border `#D7E1DE`;
- Orange `#FBAF3F` for attention/pending evidence, never as a decorative dominant color;
- Error `#B42318` only for confirmed conflict/blocking failure;
- system UI type stack with tabular numerals for money, dates, versions, counts and hashes;
- subtle borders, 6–8px radii, disciplined density and no generic AI gradient/glass treatment.

### 3.3 Signature interaction

Use one intentional visual risk: a compact **Evidence Rail `//`** running through Scope → Evidence
→ Checks → Review → Export. It encodes the real case lifecycle, indicates the current server state
and opens the relevant evidence/history panel. It must not become decorative wallpaper or a fake
progress percentage. At mobile width it becomes a semantic ordered list.

Self-critique: the previous prototype over-centred Financial Close and used broad legacy tool
surfaces. This plan narrows the signature to the shared AccountingCase lifecycle and gives each
case its own evidence projection. Financial Close is no longer the navigation root.

## 4. Locked boundaries

### Frontend may

- authenticate and obtain the current identity through existing endpoints;
- mirror capabilities to hide/disable affordances and prevent unauthorized prefetch;
- list/create/open cases within the server-authorized scope;
- attach the server-owned synthetic scenario evidence;
- request deterministic checks;
- submit typed reviewer decisions with the current immutable hashes;
- export a reviewed packet and download/render the returned artifact;
- ask the bounded Bank explanation endpoint and display its evidence/rule references;
- provide filter, comparison, explanation, accessibility and responsive presentation.

### Frontend must never

- enforce authorization as the only boundary;
- compute a financial amount, match classification, readiness verdict, severity or evidence
  completeness result;
- invent a BRAVO identifier, scope value, policy, status, source version or lineage;
- automatically retry a mutation after a revision conflict;
- silently widen scope or turn `unknown` into a plausible value;
- represent `REVIEWED` as executed or `EXPORTED` as posted/closed/locked;
- send fixture identifiers to unrelated live APIs;
- call the non-authoritative Voucher/Period preview endpoints for functional case screens;
- modify prompts, retrieval, model routing, reasoning policy, backend routes or migrations.

### Explicit non-goals

- Legacy Money Engine, Anomaly, Tax and generic Graph parity.
- A full Governance Console, billing, marketplace, Agent Catalog or agent builder.
- Live BRAVO/bank connectivity, direct database access or arbitrary SQL.
- Public/staging/production cutover.
- Conversation-quality or “better than BravoGen” claims.

## 5. Target information architecture

```text
BRAVO Accounting Intelligence
├─ Knowledge Chat
│  ├─ New conversation
│  └─ Conversations
└─ Công việc AI
   ├─ My Accounting Work
   │  ├─ Needs my attention
   │  ├─ Waiting for evidence
   │  ├─ Waiting for review
   │  ├─ Monitoring
   │  └─ Completed
   ├─ Start a job
   │  ├─ Bank Reconciliation
   │  ├─ Voucher Evidence Review
   │  └─ Period Close Readiness
   └─ Case workspace
      ├─ Scope
      ├─ Findings
      ├─ Evidence & lineage
      ├─ Recommendations
      ├─ Draft actions
      └─ Review & audit
```

Routes to implement:

| Route | Purpose |
|---|---|
| `/work` | Authorized Accounting Work inbox |
| `/work/new/:caseType` | Scope-locked start form for an enabled case type |
| `/work/cases/:caseId` | Shared durable case workspace |
| `/work/cases/:caseId/findings/:findingId` | Optional deep-link into a selected finding |
| `/accounting-work` | Temporary internal redirect to `/work` |
| `/financial-close` | Remove as product root; redirect to the Period template or isolate under QA illustration mode |

Knowledge Chat remains separately navigable. Its live conversation conversion is not a dependency
for the three-case BF-06 exit unless authentication/shell code requires the shared provider.

## 6. API and DTO contract freeze

### 6.1 Authoritative lifecycle

The functional UI uses only:

| Method and path | FE use |
|---|---|
| `GET /api/v2/accounting-cases` | inbox/list |
| `POST /api/v2/accounting-cases` | create with `scope`, `case_type`, `idempotency_key` |
| `GET /api/v2/accounting-cases/{case_id}` | authoritative refresh/deep link |
| `POST .../{case_id}/evidence` | attach or supersede server-owned synthetic evidence |
| `POST .../{case_id}/run-checks` | run deterministic checks |
| `POST .../{case_id}/review` | maker-checker review with current hashes |
| `POST .../{case_id}/export` | produce non-executing artifact |
| `POST .../{case_id}/conversation` | bounded Bank explanation/clarification only while enabled |

The legacy `/preview/voucher-review` and `/preview/period-close-readiness` endpoints are excluded.

### 6.2 Scope DTO

The create form must provide all required `ScopeKey` fields from an approved server/config source:

`tenant_id`, `legal_entity_id`, `ledger_id`, `period`, `cutoff`, `currency`, `environment`,
`bravo_version`, `config_version`, plus `bank_account_ref` for Bank when applicable.

Until the backend exposes selectable scope metadata, the local demo must use an explicitly labelled,
versioned synthetic scope preset. Free-text values cannot be presented as server-verified BRAVO
scope.

### 6.3 Case read model

Define a strict frontend `AccountingCaseView` from the current response fields:

- `case_id`, `case_type`, `scope`, `state`, `revision`;
- `evidence[]` with snapshot ID, source type/version, cutoff/captured time, content hash,
  supersession, completeness and scope;
- `results[]` with check ID, rule version, inputs, typed result, reason code and lineage IDs;
- `findings[]` with finding ID/type, severity, status, snapshot/check references and disposition;
- `review_decisions[]`;
- `draft_payload_hash`, `evidence_hash`, `result_hash`, `approval`, `trace`;
- export response `{ case, artifact }` where artifact status is
  `artifact_produced_not_executed`.

Unknown enum values render as “Không hỗ trợ bởi phiên bản UI này” and retain raw diagnostic data;
they must not fall into a success style.

### 6.4 Mutation envelope

- Generate one UUID idempotency key per user intent and retain it until the request has a terminal
  response. A transport retry reuses the same key and identical body.
- Every post-create mutation sends the last server `expected_revision`.
- On `409`, stop, refetch the case, show a revision comparison and require the user to re-apply the
  intent. Never increment the revision locally and retry.
- Review sends the current `draft_payload_hash`, `evidence_hash` and `result_hash` unchanged.
- Bank review creates one decision for every current finding. `resolved` requires evidence IDs.
- Freeze the canonical decision-hash algorithm and cross-language test vectors before enabling the
  Bank Review button: UTF-8 SHA-256 of sorted compact JSON containing finding, disposition,
  reviewer, reason, note and evidence snapshot IDs.
- Export uses only the hash envelope returned by the reviewed case. A superseded case invalidates
  the previous review/export affordance.

### 6.5 Error grammar

| Status | UI behavior |
|---|---|
| `401` | clear session, preserve a safe return URL, go to sign-in |
| `403` | permission boundary; do not reveal counts/content |
| `404` capability disabled | show unavailable for this environment; no fallback preview |
| `409` | revision/idempotency/state conflict; refetch and compare |
| `422` | field-level invalid request or contract mismatch; retain user input |
| `5xx`/network | recoverable error; no optimistic accounting-state change |

## 7. Frontend module target

```text
FigmaMake_UI/src/
  app/                    router, providers, protected shell, error boundaries
  api/                    client, auth, errors, AccountingCase DTOs/services
  auth/                   session, login, OIDC callback, /api/me
  capabilities/           presentation-only permission mirror
  design/                 tokens, primitives, theme, Evidence Rail
  accounting-work/
    inbox/                filters, rows, empty/denied/error states
    create/               enabled templates and synthetic scope preset
    case-shell/           tabs, header, lifecycle actions, revision banner
    bank/                 match/finding/review/explanation projections
    voucher/              evidence/check/review packet projections
    period-close/         prerequisite/blocker/readiness projections
    review/               decisions, maker-checker, hash envelope
    evidence/             snapshot/lineage/supersession inspector
    export/               artifact preview/download and non-execution label
  conversation/           existing prototype retained behind its own boundary
  fixtures/               QA-only scenarios; hard network guard
  test/                   MSW or fetch mocks, contract vectors, axe, visual/E2E
```

No component calls `fetch` directly. Components consume typed query/command services. Live and QA
fixture providers are separate at the provider boundary and cannot return a mixed array.

## 8. Work packages and dependency order

| WP | Work package | Status | Depends on |
|---|---|---|---|
| FEV2-00 | Admission decision and baseline | `COMPLETE` | BF-00..05 |
| FEV2-01 | Contract snapshot, DTOs and API foundation | `COMPLETE` | FEV2-00 |
| FEV2-02 | Real auth, identity and protected shell | `COMPLETE` | FEV2-01 |
| FEV2-03 | Accounting Work inbox and case creation | `COMPLETE` | FEV2-02 |
| FEV2-04 | Shared case workspace and lifecycle controls | `COMPLETE` | FEV2-03 |
| FEV2-05 | Bank Reconciliation deep UX | `COMPLETE` | FEV2-04 |
| FEV2-06 | Voucher functional UX | `COMPLETE` | FEV2-05 shared contracts |
| FEV2-07 | Period Close functional UX | `COMPLETE` | FEV2-05 shared contracts |
| FEV2-08 | Concurrency, denial and supersession hardening | `COMPLETE` | FEV2-05..07 |
| FEV2-09 | Integrated E2E, a11y, visual and build evidence | `COMPLETE — browser/local fixture scope` | FEV2-08 |
| FEV2-10 | Local demo handoff and rollback evidence | `COMPLETE — DEMO18-08/09 live two-identity, hashes and rollback evidence` | FEV2-09 |

### 8.1 Completion reconciliation (2026-08-03)

The current status table is reconciled by Plan 18's final evidence packet. The detailed unchecked
lists in FEV2-02 through FEV2-09 remain the historical pre-execution ledger and must not override
the evidence-indexed status. FEV2-10 is complete only for the local synthetic technical handoff;
it does not record owner acceptance, a pilot, customer-data authority or production release.

Only one package is `IN_PROGRESS`. Update this table, the evidence index and handoff at each stop.

### FEV2-00 — admission and baseline — complete

- [x] Accept Plan 16 BF-00 through BF-05 developer evidence.
- [x] Record `FE ADMISSION OPEN` with its local-synthetic boundary.
- [x] Record current dirty-worktree baseline and Alembic head `0020_case_v2_audit`.
- [x] Verify candidate typecheck, 4 files/8 tests and production build.
- [x] Preserve `frontend-react` as untouched comparator/rollback.

Exit: Plan 16 BF-06 may begin without implying external-gate completion.

### FEV2-01 — contract snapshot and runtime foundation

- [x] Freeze the AccountingCase API subset and representative success/error grammar in
  `FigmaMake_UI/contracts/ACCOUNTING-CASE-API-V1.md`.
- [x] Add exact TypeScript DTOs and runtime validation for all case responses.
- [x] Add typed API client, bearer header, normalized error union and abort handling.
- [x] Add idempotency-key lifecycle and deterministic decision-hash test vectors.
- [x] Add live-vs-QA provider separation and keep fixture code's zero-network enforcement.
- [x] Replace the 171-case registry's Financial Close/product-root assumptions with three-case
  Accounting Work coverage while preserving deterministic IDs.
- [x] Add the `test:contract` script. Browser E2E runner/configuration intentionally begins in
  FEV2-09 with the local protected-route/auth environment; no placeholder `test:e2e` script is
  added or reported as evidence.

Exit: strict decoded/mocked lifecycle boundary, hash vector, fixture-ID rejection and
`403/404/409/422` behavior pass without rendering a screen. Browser/API lifecycle E2E begins only
after the protected shell exists.

### FEV2-02 — real auth, identity and shell

- [ ] Replace fake sign-in with `/api/auth/config`, password login, OIDC fragment handling,
  `/api/me`, logout and `401` expiry.
- [ ] Use a candidate-specific sessionStorage namespace; do not share mutable router/store state
  with the classic frontend.
- [ ] Implement protected deep links and validated `next` handling.
- [ ] Derive presentation capabilities from `is_admin` and `accounting_case:{read|create|review}:*`.
- [ ] Prevent unauthorized route prefetch and count leakage; backend remains authoritative.
- [ ] Rework navigation around Knowledge Chat and `Công việc AI`; remove Financial Close as root.
- [ ] Preserve responsive shell, light/dark/system, focus lifecycle and reduced motion.

Exit: maker, reviewer, admin, denied and expired-session contract tests pass at 1440/1024/390.

### FEV2-03 — inbox and case creation

- [ ] Build `/work` from `GET /api/v2/accounting-cases` with server data only.
- [ ] Map server states to the five inbox filters without changing underlying state.
- [ ] Render type, locked scope, state, owner/reviewer availability where supplied, revision and
  attention reason. Do not invent SLA, value or risk scores.
- [ ] Build three enabled templates and a versioned synthetic scope preset.
- [ ] Create with one idempotency key; support pending, duplicate-click suppression, `403/409/422`.
- [ ] Deep-link immediately to the returned case ID.

Exit: two authorized identities see only server-authorized cases; empty and denied remain distinct.

### FEV2-04 — shared case workspace

- [ ] Build one shared header with case type, state, revision, synthetic origin and scope lock.
- [ ] Build the six required tabs and the semantic Evidence Rail.
- [ ] Add evidence snapshot inspector with content hash abbreviation/copy, version, cutoff, captured
  time, completeness, lineage and supersession chain.
- [ ] Add deterministic result and finding primitives that retain rule/reason codes.
- [ ] Gate actions from server state plus presentation capability; server errors always win.
- [ ] Implement attach/supersede evidence and run-check actions with revision/idempotency controls.
- [ ] Refetch on focus/reconnect and expose stale local projection before accepting a mutation.

Exit: shared shell covers every CaseState and all required missing/stale/superseded/conflict/
abstained/denied/unresolved states without case-specific business logic in the shell.

### FEV2-05 — Bank Reconciliation deep UX

- [ ] Summary: evidence coverage/control totals and match classification counts from server results.
- [ ] Findings: exact/tolerance/aggregate/duplicate/bank-only/BRAVO-only/ambiguous/invalid projections
  with contributing evidence and rule lineage.
- [ ] Candidate conflicts remain conflicts; UI cannot select or relabel an exact match outside a
  typed reviewer disposition.
- [ ] Reviewer form covers every finding, reason/note, resolution evidence and maker-checker denial.
- [ ] Implement canonical decision hashes and bind review to current payload/evidence/result hashes.
- [ ] Add bounded explanation panel showing returned finding/evidence/rule IDs and `mutates_case=false`.
- [ ] Export packet preview prominently states `artifact_produced_not_executed`.

Exit: Bank completes create → evidence → checks → second-user review → export through the local API;
competition, supersession and stale-review E2E cases fail closed.

### FEV2-06 — Voucher Evidence Review

- [ ] Present immutable invoice, PO/contract, receipt/QC, BRAVO draft-voucher and policy snapshots.
- [ ] Render total, tax, duplicate, three-way, supplier/master, account/dimension and evidence
  coverage checks from server results.
- [ ] Provide line-level mismatch/evidence lineage without implementing tax or accounting math in JS.
- [ ] Reuse shared review/export controls; no second case state machine or approval component.
- [ ] Show abstention for missing/inapplicable evidence and keep the no-post boundary persistent.

Exit: functional durable lifecycle passes; fabricated IDs/caller scalars have no UI path.

### FEV2-07 — Period Close Readiness

- [ ] Present the server-authoritative prerequisite/dependency matrix, freshness, approvals and
  reconciliation references.
- [ ] Make readiness a reasoned status with explicit blockers, never a decorative percentage.
- [ ] Link Bank case references without exposing unauthorized case metadata.
- [ ] Reuse shared review/handoff export; no depreciation, costing, FX, close, report or lock controls.
- [ ] Move the old Financial Close illustration behind QA-only reference or remove it after approved
  visual migration; do not mix its fixture state with the functional Period case.

Exit: empty, omitted, stale, wrong-scope and unresolved-material states visibly block readiness;
the complete synthetic scenario can reach reviewed/exported without implying BRAVO close.

### FEV2-08 — hard-state and security UX

- [ ] Exercise two users/two departments, maker/reviewer, admin/non-admin and capability-disabled
  responses with deterministic fixtures plus local API E2E where available.
- [ ] Add revision-conflict refetch/diff/re-apply flow and duplicate transport retry with the same key.
- [ ] Invalidate review/export controls immediately after evidence supersession.
- [ ] Ensure `403` and scoped `404` do not disclose hidden counts, labels or lineage.
- [ ] Prevent fixture IDs from leaving QA providers and scrub case data from client logs/errors.
- [ ] Add route-level error boundaries and offline/limited-capability behavior without silent cloud
  fallback.

Exit: no optimistic success survives a failed server response; no denied metadata appears in DOM,
prefetch or error copy.

### FEV2-09 — integrated verification

- [ ] Typecheck and unit/contract tests from the frozen lockfile.
- [ ] Local API E2E for each three-case lifecycle plus 401/403/404/409/422/5xx.
- [ ] Axe/WCAG 2.2 AA checks on every route and hard state.
- [ ] Keyboard-only review/export, drawer/dialog focus trap and restore, skip links and live regions.
- [ ] 200% zoom and minimum 44px mobile targets.
- [ ] Screenshot comparison at 1440×900, 1024×768, 768×1024 and 390×844 in light/dark.
- [ ] Production build, route deep-link serving, refresh and asset-base verification through FastAPI.
- [ ] Confirm initial `/work` bundle excludes legacy tools, graph/diagram packages and unused heavy
  dependencies.
- [ ] Re-run classic frontend typecheck/test/build without modifying it.

Exit: all automated FE gates pass and visual/a11y findings have dispositions and evidence paths.

### FEV2-10 — local demo handoff and rollback

- [x] Produce an immutable candidate bundle and checksum manifest.
- [x] Preserve an immutable classic bundle and documented selector/rollback procedure.
- [x] Run the technical rehearsal: maker creates/checks; different reviewer reviews/exports all three cases.
- [x] Record known limitations and deferred external gates in the demo itself and evidence index.
- [x] Keep production/static cutover disabled.

Exit: council may record “local synthetic three-case developer demo ready for human evaluation”.
No stronger release claim follows automatically.

## 9. State-to-UI rules

| Server state | Primary UI meaning | Allowed primary action |
|---|---|---|
| `NEW`, `SCOPE_LOCKED`, `EVIDENCE_PENDING` | scope locked; evidence not ready | attach/refresh evidence if authorized |
| `EVIDENCE_READY` | required snapshot set available | run checks |
| `CHECKED`, `NEEDS_REVIEW` | deterministic results exist; human disposition pending | review for eligible non-maker |
| `REVIEWED` | exact packet/hash envelope approved | export if authorized |
| `EXPORTED` | artifact produced, not executed | inspect/download artifact |
| `ABSTAINED` | insufficient authoritative evidence/policy | inspect reason and next evidence action |
| `FAILED` | explicit processing failure | inspect error; safe retry only as a new user intent |
| `SUPERSEDED` | evidence/result/review invalidated | return to current evidence lifecycle |
| `CANCELLED`, `CLOSED` | no further mutation | read-only audit/history |

These are presentation rules, not an alternate frontend state machine.

## 10. Verification commands

Use the actual package scripts; update this section only when the repository changes.

```powershell
Set-Location FigmaMake_UI
pnpm.cmd install --frozen-lockfile
pnpm.cmd run typecheck
pnpm.cmd run test
pnpm.cmd run test:contract
pnpm.cmd run test:a11y
pnpm.cmd run test:visual
pnpm.cmd run build
```

`test:visual` must eventually perform screenshot comparison; the current manifest-only test is a
coverage assertion and cannot be reported as visual regression evidence. Browser `test:e2e` is
introduced in FEV2-09, after the local protected-route/auth environment exists.

Classic comparator:

```powershell
Set-Location frontend-react
npm.cmd ci
npm.cmd run typecheck
npm.cmd test -- --run
npm.cmd run build
```

Repository hygiene:

```powershell
git status --short
git diff --check
git diff -- FigmaMake_UI
git diff -- frontend-react
```

## 11. Evidence index to produce

- admission decision and packet;
- OpenAPI subset checksum and example DTO fixtures;
- cross-language decision-hash vectors;
- route/state/capability matrix;
- three lifecycle contract/E2E reports;
- maker-checker and two-user/two-department negative evidence;
- revision/idempotency/supersession evidence;
- axe, keyboard, zoom and responsive evidence;
- screenshot baselines/diffs in both themes;
- candidate/classic build hashes and rollback instructions;
- final local-demo gate result with deferred external gates.

## 12. Stop conditions

Stop and request owner/council direction when:

- the UI needs caller-asserted accounting truth to produce a positive case;
- the existing API cannot expose a required state without a backend contract change;
- a server response cannot be mapped without recalculating accounting logic in the browser;
- maker-checker, RLS, evidence/hash or revision/idempotency controls would be weakened;
- live and QA fixture projections cannot be separated reliably;
- a case requires recreating BRAVO voucher, ledger, calculation, report, approval or lock behavior;
- any P0/P1 scope leak, unsafe mutation, approval bypass or false positive remains;
- offline build or local same-origin operation requires uncontrolled network access;
- work expands into legacy tool parity, prompt/retrieval/model changes or production cutover.

## 13. Definition of done

Plan 17 is complete only when:

1. `FigmaMake_UI` uses real auth/identity and the durable V2 case API for all three cases.
2. One shared inbox and case workspace cover every required state and six-tab contract.
3. Accounting verdicts, evidence, hashes, revision and maker-checker remain backend-owned.
4. Missing/stale/superseded/conflicted/abstained/denied/unresolved paths fail closed.
5. Bank, Voucher and Period complete their local two-user reviewed export lifecycle.
6. Typecheck, unit/contract, local E2E, accessibility, visual and production-build gates pass.
7. `frontend-react` remains runnable and unchanged with an immutable rollback artifact.
8. The demo says synthetic/non-executing everywhere required and makes no external-gate claim.

## 14. First implementation handoff

```text
Objective:
Implement FEV2-02 in FigmaMake_UI only.

Starting truth:
- FE ADMISSION OPEN is limited to local synthetic three-case integration.
- Alembic head is 0020_case_v2_audit.
- Candidate typecheck, 5 files/15 tests, `test:contract`, accessibility smoke and build pass.
- FEV2-01 froze the AccountingCase API contract, strict decoder, typed client, hash vector and
  fixture/live data-source separation.
- Auth/AppContext and AccountingWork are still fixture-owned.
- frontend-react is comparator/rollback and must not be edited.

First actions:
1. Add a candidate-scoped auth/session provider using `/api/auth/config`, password login,
   OIDC fragment handoff and `/api/me`.
2. Replace fake protected-route admission outside `?qa=1`; preserve QA-only fixture access.
3. Derive presentation capabilities from the returned identity without changing backend authority.
4. Rework shell navigation around Knowledge Chat and Accounting Work; keep Financial Close out of
   the product root.
5. Add login, expiry, protected deep-link and denied-prefetch tests.

Do not:
- use preview endpoints;
- compute accounting results in TypeScript;
- edit backend, migrations, prompts, retrieval or frontend-react;
- report local FE work as SME/model/pilot/production evidence.
```
