# BRAVO V2 Figma Make — UI-first development tracker

Status: `ACTIVE — FE PROTOTYPE ONLY; OWNER APPROVAL REQUIRED BEFORE INTEGRATION`
Owner: project owner
Working application: `FigmaMake_UI/`
Classic comparator/rollback: `frontend-react/` — read-only during this phase
Repository baseline: `feat/v2-p0-containment` at `f17d31c079f8de71f0ffc303495f3176eef59d23`
Created: 2026-07-21
Last updated: 2026-07-21
Current package: `UI-11 — READY_FOR_REVIEW`
Next package after owner review: `INT-00 — remains LOCKED until section 16 records APPROVED`

---

## 1. Owner direction captured by this tracker

Develop and review the new BRAVO frontend in an **UI-first, fixture-driven phase** before connecting
it to the existing platform runtime.

The first delivery is not a backend-integrated application. It is a complete, navigable and
reviewable frontend prototype that lets the owner inspect:

- every required page and important subview;
- normal, loading, empty, error, permission and exceptional states;
- realistic end-to-end user journeys for each BRAVO role;
- responsive behavior, themes, keyboard behavior and Vietnamese product copy;
- the correct BRAVO business meaning of evidence, financial readiness, drafts and approvals;
- explicit mock/fixture labels so illustration data is never mistaken for live ERP data.

After the frontend review package is complete, development **must stop**. Auth, API, SSE and live
service integration may begin only after the owner records an explicit `APPROVED` decision in
section 16.

### 1.1 Relationship to the cutover plan

`plan-rebuild/09-FRONTEND-FIGMA-MAKE-CUTOVER-EXECUTION-PLAN.md` remains the authority for later
runtime integration, verification, staging, cutover and rollback.

For the current phase, this tracker changes execution order as follows:

```text
Old immediate sequence in plan 09
FM-01 runtime boundary -> auth/API/SSE integration -> complete remaining surfaces

Owner-approved UI-first sequence
complete mock/fixture FE -> owner visual/functional review -> STOP
                                      |
                                      `-- only after APPROVED: resume FM-01..FM-08
```

Do not edit or mark FM-01 `IN_PROGRESS` while this tracker is in an unapproved UI-first phase.

## 2. Authority, precedence and evidence rules

Use this order when resuming UI work:

1. `docs/PROJECT-STATE.md`
2. `docs/AI-REVIEW-MANIFEST.md`
3. `plan-rebuild/08-V2-CONVERSATION-REBUILD-HANDOFF.md`
4. `plan-rebuild/04-WORKSPACE-REPO-COUNCIL-DECISION.md`
5. `plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`
6. `plan-rebuild/09-FRONTEND-FIGMA-MAKE-CUTOVER-EXECUTION-PLAN.md`
7. `FigmaMake_UI/AGENTS.md`
8. `FigmaMake_UI/src/imports/DESIGN.md`
9. `FigmaMake_UI/PRODUCT-LOGIC.md`
10. `FigmaMake_UI/DESIGN-QA-RESULTS.md`
11. this tracker
12. current code/tests/runtime evidence for any disputed claim

Precedence within the UI-first phase:

1. Security, authorization, evidence, financial-integrity and approval invariants cannot be
   weakened by a UI decision.
2. Current code and API behavior override historical prose when describing existing capability.
3. This tracker controls FE-only work order and review status.
4. Plan 09 controls the post-approval integration/cutover program.
5. Existing Figma screens are a visual starting point, not proof that all product cases are done.

## 3. Phase boundary

### 3.1 Allowed now

- Edit files only inside `FigmaMake_UI/` for the new visual experience.
- Create/refine pages, components, design tokens, fixture state, mock services and local routing.
- Add deterministic fixture scenarios and automated frontend tests.
- Use React Router locally so every review state has a stable URL.
- Create realistic but synthetic Vietnamese examples with unmistakable illustration labels.
- Read `frontend-react/`, backend routes and tests to verify a named business or compatibility
  contract.
- Run typecheck, unit, component, accessibility, visual and production-build verification.

### 3.2 Forbidden until owner approval

- Do not connect login to real password/OIDC or `/api/me`.
- Do not send real API requests, open a real SSE stream or upload to a real endpoint.
- Do not implement real approval/rejection/export, draft creation or any ERP mutation.
- Do not change backend routes, models, prompts, retrieval, routing, critic, synthesis or migrations.
- Do not modify `frontend-react/`, Docker, CI or production static serving.
- Do not start FM-01..FM-08 implementation work from plan 09.
- Do not describe mock behavior as integrated, authorized, executed or verified.

### 3.3 Absolute product invariants

- Authorization/RLS is enforced outside the model and outside presentation logic.
- Frontend role/capability fixtures demonstrate affordances only; they never prove access control.
- Exact financial, schema, version and execution claims require matching evidence.
- `draft != validated != approved != exported != executed != verified`.
- Approved never means executed, and completed advisory work never means an ERP action ran.
- Generated SQL, config, accounting entries and exports are never executed automatically.
- Company, branch, period, environment and BRAVO version remain `Chưa xác định` when unknown.
- The verified offline-capable path and controlled cloud-egress boundary remain visible in UX.
- UI work makes no claim about Conversation Core V2 answer quality or A/B/C/D results.

## 4. How AI developers must use this file

This document is the single tracking surface for the UI-first phase.

At the start of every development session:

1. Read the required context in section 2.
2. Run `git status --short`; preserve all unrelated and untracked user work.
3. Read the dashboard, the active package and the last handoff in sections 5, 14 and 17.
4. Confirm no real integration work is being introduced.
5. Mark exactly one package `IN_PROGRESS`.

Before stopping:

1. Update the package checklist and dashboard status.
2. Add commands/results and review artifacts to the evidence log.
3. Record any accepted owner decision; do not infer approval from silence.
4. Run `git diff --check` and confirm `git diff -- frontend-react` is empty.
5. Replace the handoff block with the next exact action and known limitations.

Allowed package statuses:

| Status | Meaning |
|---|---|
| `NOT_STARTED` | No implementation evidence exists. |
| `IN_PROGRESS` | The only package currently being edited. |
| `BLOCKED_OWNER` | A product choice changes visible scope/behavior and awaits owner input. |
| `BLOCKED_EVIDENCE` | Current BRAVO behavior cannot yet be established from code/tests. |
| `READY_FOR_REVIEW` | Package checks pass and review URLs/states are listed. |
| `CHANGES_REQUESTED` | Owner reviewed and requested corrections. |
| `APPROVED` | Owner explicitly accepted the package. |

Never use `COMPLETE` for a package that the owner has not reviewed when owner review is part of its
exit criteria.

## 5. Master dashboard

Only one row may be `IN_PROGRESS`.

| ID | Package | Status | Depends on | Owner review |
|---|---|---|---|---|
| UI-00 | Tracker, scope freeze and current-surface inventory | `APPROVED` | — | Owner directed implementation |
| UI-01 | Prototype foundation, design system, route shell and QA controls | `READY_FOR_REVIEW` | UI-00 | Required |
| UI-02 | Sign-in, session-boundary and protected-navigation mock UX | `READY_FOR_REVIEW` | UI-01 | Required |
| UI-03 | New conversation, history and active conversation cases | `READY_FOR_REVIEW` | UI-01 | Required |
| UI-04 | Financial Close readiness, evidence and dependency graph | `READY_FOR_REVIEW` | UI-01, UI-03 | Required |
| UI-05 | Draft and approval review | `READY_FOR_REVIEW` | UI-01 | Required |
| UI-06 | Knowledge library and governed document cases | `READY_FOR_REVIEW` | UI-01 | Required |
| UI-07 | Administration and audit | `READY_FOR_REVIEW` | UI-01 | Required |
| UI-08 | Money Engine, Anomaly, Tax and generic Knowledge Graph parity | `READY_FOR_REVIEW` | UI-01, UI-05 | Required |
| UI-09 | Shared/read-only surface, not-found and route aliases | `READY_FOR_REVIEW` | UI-01, UI-03 | Required |
| UI-10 | Cross-route async states, roles, responsive, theme and accessibility | `READY_FOR_REVIEW` | UI-02..UI-09 | Required |
| UI-11 | Owner review pack and FE-only acceptance gate | `READY_FOR_REVIEW` | UI-10 | Final decision |
| INT-00 | Post-approval integration re-planning against FM-01..FM-08 | `LOCKED` | UI-11 `APPROVED` | Separate approval |

## 6. Current prototype inventory

This is the verified starting inventory, not an acceptance result.

| Surface/capability | Current state | UI-first work still required |
|---|---|---|
| Sign in | `PARTIAL` | SSO/password variants, validation, forgot-password handoff, expiry/return cases |
| Responsive application shell | `PARTIAL` | Stable routes, full theme system, all role/capability combinations, account menu |
| New conversation | `PARTIAL` | Recent-history cases, draft prompt/attachment states, invalid/blocked inputs |
| Active conversation | `PARTIAL` | Full stream lifecycle, edit/regenerate, feedback/report, share, uploads and recovery |
| Financial Close readiness | `PARTIAL — strong visual baseline` | Complete scenario matrix, applicability, stale/revision cases and owner review |
| Financial Close graph | `PARTIAL — strong visual baseline` | Complete controls, cross-linking, permission boundary, list/table parity |
| Draft approval | `PARTIAL` | Queue filters, full lifecycle, conflict/revision/negative maker-checker cases |
| Knowledge library | `PARTIAL` | Upload/delete/file preview flows, visibility, ingestion and governance cases |
| Administration | `PARTIAL` | Current-product page model, empty/error/403, no invented governance metadata |
| Conversation list/history route | `MISSING/PARTIAL` | Dedicated mobile/compact experience and history operations |
| Money Engine | `MISSING` | Complete fixture-driven parity page |
| Anomaly | `MISSING` | Complete fixture-driven parity page |
| Tax | `MISSING` | Complete fixture-driven parity page |
| Generic Knowledge Graph | `MISSING` | Separate from Financial Close graph |
| Shared read-only conversation | `MISSING` | Valid/expired/revoked/invalid token states |
| Not found/route aliases | `MISSING` | Safe redirects and clear unavailable state |
| Automated unit/a11y/visual tests | `MISSING` | Add during UI-01 and extend per package |
| Light/Dark/System themes | `MISSING/PARTIAL` | Flash-free theme initialization and complete visual checks |

## 7. Canonical page and route map for FE review

Routes are local prototype routes backed only by fixtures in this phase. A route's presence does
not imply a matching backend endpoint.

| Priority | Route | Page | Required variants/actions |
|---|---|---|---|
| P0 | `/login` | Sign in | SSO enabled/disabled; password enabled/disabled; validation; loading; failure; support |
| P0 | `/` | New conversation | task starters; recent history; empty history; composer; attachment/profile affordances |
| P0 | `/c/:id` | Active conversation | load; stream; stop; retry; citations; evidence; drafts; task state; edit/regenerate |
| P0 | `/conversations` | Conversation history | list; search; empty; load error; compact/mobile selection; new conversation |
| P0 | `/financial-close` | Close readiness | eight governed groups; filters; node detail; safe next action; status reason |
| P0 | `/financial-close/graph` | Close evidence graph | graph/list/table; search; filters; inspector; focus/reset; accessible traversal |
| P0 | `/approvals` | Draft queue/review | queue; detail; before/after; validation; approve/request changes/reject; audit |
| P0 | `/knowledge` | Knowledge library | scopes; search/filter; upload simulation; detail/file simulation; governance status |
| P1 | `/admin` | Administration | users/departments/permissions; usage; feedback; audit; health; policy read-only views |
| P1 | `/tools/money-engine` | Money Engine | invoice upload simulation; draft review; filters; select; export simulation |
| P1 | `/tools/anomaly` | Anomaly | scan simulation; result queue; investigation confirmation; reject/reason |
| P1 | `/tools/tax` | Tax | reconciliation simulation; result queue; recommendation draft review |
| P1 | `/tools/knowledge-graph` | Generic graph | live-contract-shaped fixture; source open simulation; Ask AI handoff |
| P1 | `/shared/:token` | Shared conversation | read-only answer/evidence; valid, expired, revoked, invalid and permission-safe cases |
| P1 | `*` | Not found | clear recovery action; never expose hidden navigation or data |

Post-approval alias candidates for compatibility: `/documents -> /knowledge`,
`/drafts -> /approvals`, `/money-engine -> /tools/money-engine`, `/anomaly -> /tools/anomaly`,
`/tax -> /tools/tax`, and `/graph -> /tools/knowledge-graph`.

### 7.1 Route-by-route classic parity contract

`Future contract reference` is read-only information for fixture shape and later integration. It
does not authorize network calls in the UI-first phase.

| Target route | Classic route/surface | Existing behavior that must not disappear | UI-first fixture parity set | Future contract reference | Initial parity |
|---|---|---|---|---|---|
| `/login` | `/login` | Auth config discovery, password login, OIDC entry, safe protected redirect, unauthorized return | AUTH-01..AUTH-08; SSO/password configurations; invalid and expired session | `/api/auth/config`, `/api/auth/login`, `/api/auth/oidc/login`, `/api/me` | `PARTIAL` |
| `/` | `/` | Start new conversation, choose Consultant profile, enter prompt, stage files/invoice, show recent conversations | empty/recent history; valid/invalid prompt; profile options; attachment/invoice states | `/api/conversations`, `/api/attachments`, `/api/invoices/draft` | `PARTIAL` |
| `/c/:id` | `/c/:id` | Load owned conversation; message stream; plan/status/tool/artifact/source/draft events; stop; upload; feedback/report; edit/regenerate/truncate; share | CHAT-01..CHAT-30 and SSE-01..SSE-18 | `/api/conversations/{id}`, `/api/chat/{id}/messages`, `/api/agent-runs/{run}/cancel`, message feedback/truncate/share APIs | `PARTIAL` |
| `/conversations` | classic sidebar | List, select, delete and start new; preserve title and recency | HIST-01..HIST-10 including rename-shaped UX, delete confirm and pagination/large list presentation | `/api/conversations`, `/api/conversations/{id}`, `/api/conversations/{id}/rename` | `MISSING/PARTIAL` |
| `/knowledge` | `/documents` | Mine/department/global scopes; optional knowledge label; visibility; upload; delete owned source | KNOW-01..KNOW-15; detail/preview; ownership; upload progress; dedupe; ingestion states | `/api/sources`, `/api/sources/{id}`, `/api/sources/{id}/file` | `PARTIAL` |
| `/approvals` | `/drafts` and chat draft card | Status/kind list; review; approve/reject; select approved journals; single CSV/XLSX and batch export | DRAFT-01..DRAFT-18; maker-checker; revision; mixed selection; export failure | `/api/drafts`, `/api/drafts/{id}`, approve/reject and export APIs | `PARTIAL` |
| `/admin` | `/admin` | Users, departments, permission catalogue, usage, disliked feedback, create user/department, reset password | ADMIN-01..ADMIN-12; independent state boundaries; validation; duplicate/conflict cases | `/api/admin/users`, `/api/admin/departments`, `/api/admin/permissions`, `/api/admin/usage`, `/api/admin/feedback` | `PARTIAL` |
| `/tools/money-engine` | `/money-engine` | XML invoice upload, journal draft list/filter/detail, approve/reject, eligible batch export | MONEY-01..MONEY-10; multi-file partial failure; imbalanced/needs-review; export eligibility | `/api/invoices/draft`, `/api/drafts` and draft action/export APIs | `MISSING` |
| `/tools/anomaly` | `/anomaly` | Start scan, show count/result draft flags, severity, confirm investigation, dismiss | ANOM-01..ANOM-08; no-source, busy, partial failure, stale result, reviewer boundary | `/api/agents/anomaly/scan`, `/api/drafts?kind=anomaly_flag` | `MISSING` |
| `/tools/tax` | `/tax` | Start reconcile, source-needed guidance, result adjustment drafts, create recommendation/dismiss | TAX-01..TAX-08; no evidence, mismatch, no findings, review boundary, chat handoff | `/api/agents/tax/reconcile`, `/api/drafts?kind=tax_adjustment` | `MISSING` |
| `/tools/knowledge-graph` | `/graph` | Load graph, group filters, similarity threshold, search/locate, zoom/fit/relayout/reload, source open, Ask AI | KGRAPH-01..KGRAPH-10; empty/error/403; inaccessible source; accessible list/table fallback | `/api/graph`, `/api/sources/{id}/file` | `MISSING` |
| `/financial-close` | no classic equivalent | New V2 fixture surface; must preserve Conversation Core prerequisite and evidence invariants | CLOSE-01..CLOSE-13 | No current live endpoint; remain fixture-only even after general integration until separately approved | `PARTIAL` |
| `/financial-close/graph` | no classic equivalent | New V2 fixture projection; distinct from generic graph | CLOSE-09..CLOSE-13 plus graph/list/table quality cases | No current live endpoint; do not map to `/api/graph` | `PARTIAL` |
| `/shared/:token` | `/shared/:token` | Public token-shaped read-only transcript, loading and invalid-link handling | SHARE-01..SHARE-06; no protected shell; evidence safe; revoked/expired | `/api/shared/{token}` | `MISSING` |
| `*` | classic redirect to `/` | Unknown route cannot expose data; user can recover safely | ROUTE-01..ROUTE-05; signed-in/out variants; malformed IDs; safe alias behavior | SPA fallback only | `MISSING` |

Parity means the accepted candidate provides an equal or safer user-visible ability. It does not
require copying the classic layout, preserving classic implementation defects or exposing a
capability to a role that the backend would deny.

### 7.2 Non-route capabilities that must remain reachable

These are embedded flows, drawers, cards or dialogs rather than primary navigation routes.

| Capability | Entry surface | Required UI-first cases | Parity rule |
|---|---|---|---|
| Conversation evidence/citations | Assistant answer | none, one, many, stale, conflict, inaccessible source, mobile sheet | Opening evidence preserves reading position and does not imply verification. |
| Agent plan and progress | Active conversation | initial plan, plan update, current status, completed/failed tool result | Present useful status without exposing chain-of-thought. |
| Artifacts | Assistant answer | artifact announced, metadata load, unavailable, download failure | Artifact is not proof of execution; title/kind/origin are visible. |
| Draft card | Assistant answer and Approvals | proposed, validation failed, ready, approved, rejected, exported | Same lifecycle language and review rules in both entry points. |
| Attachment tray | New/active composer | upload, pending processing, ready, failed, remove, unsupported, too large | Sending is blocked only when necessary; typed prompt is preserved. |
| Invoice detail | Conversation and Money Engine | valid draft, parse warning, needs review, unbalanced, failed | Financial values are fixture-labelled and tabular. |
| Consultant task strip | Active conversation | active, paused, completed advisory, cancelled; wrong goal/step/unsafe feedback | Completion never means ERP execution; profile never widens permission. |
| Share management | Active conversation | create, copy, existing link, revoke, failure | Shared output is read-only and token contents are never logged/displayed. |
| Message feedback | Assistant answer | like, dislike, clear selection, report category/comment, failure/retry | Optimistic UI must visibly recover on simulated failure. |
| Edit/regenerate | User/assistant message | last turn, earlier turn, confirm truncation, failure/rollback | Downstream local turns are removed consistently and task revision implications are visible. |
| Account menu | Shell | identity summary, theme, logout, password-change handoff where permitted | Role/capability are descriptive fixtures, not an authorization control. |
| Offline/egress boundary | Shell and affected answer | offline local, limited capability, cloud blocked, recovery | Unavailable evidence remains unconfirmed; no silent cloud fallback. |

### 7.3 SSE/event presentation parity for the later live contract

The UI-first phase uses a deterministic mock event scheduler with these event-shaped fixtures. No
real stream is opened.

| ID | Event/case | Required presentation and state effect |
|---|---|---|
| SSE-01 | `id` | Associate mock conversation/run IDs once; stable URL transition; reject a late ID after cancel. |
| SSE-02 | `plan` | Render an initial concise work plan without exposing hidden reasoning. |
| SSE-03 | `plan_update` | Update existing plan in place; do not duplicate steps or reset the answer. |
| SSE-04 | `status` | Announce useful current activity through a stable, accessible status region. |
| SSE-05 | `step` | Add normalized progress; repeated/out-of-order fixture is handled deterministically. |
| SSE-06 | `tool_call` | Show a safe operation label only; redact/omit sensitive arguments in presentation fixtures. |
| SSE-07 | `tool_result` success | Mark operation complete with bounded summary; no execution overclaim. |
| SSE-08 | `tool_result` error | Mark recoverable/terminal error accurately; preserve prior stream state. |
| SSE-09 | `source` | Merge citation identifiers without duplicate chips and without inventing source metadata. |
| SSE-10 | `attachments` | Attach server-shaped filenames/kinds to the user turn; do not reveal local paths. |
| SSE-11 | `artifact` | Add a reviewable artifact reference; unavailable download is a distinct case. |
| SSE-12 | `draft` | Render a governed draft card; never auto-approve or auto-export. |
| SSE-13 | `answer` | Append delta without layout jump; preserve whitespace/Markdown safety. |
| SSE-14 | `ping` | No visible message; only keeps mock stream active. |
| SSE-15 | `done` normal | Finalize answer, grounded/cloud/clarify metadata and message IDs exactly once. |
| SSE-16 | `done` stopped | End as stopped, keep partial answer clearly incomplete, permit retry. |
| SSE-17 | `error` | Present normalized error; do not treat it as an assistant answer. |
| SSE-18 | late/duplicate/out-of-order event | Ignore events owned by cancelled/older run and prevent duplicate artifacts/drafts/citations. |

### 7.4 Route parity review states

Every route must publish direct QA URLs for applicable state keys. This prevents a page from being
declared done after reviewing only the default fixture.

```text
?qa=1
&role=<accountant|chief_accountant|finance_manager|consultant|administrator>
&capability=<online|offline_local|limited_capability|cloud_blocked>
&scenario=<stable-scenario-id>
&state=<loading|ready|empty|error|permission_denied|session_expired|stale|conflict|offline>
&theme=<light|dark|system>
```

Required state applicability matrix:

| Route family | loading | empty | error | 403 | expiry | offline | stale/conflict | revision conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Login | Yes | N/A | Yes | N/A | N/A | Yes | N/A | N/A |
| Conversation/history | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes for task-changing actions |
| Financial Close | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Approvals/drafts | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Knowledge | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes for mutations |
| Admin | Yes per section | Yes per section | Yes per section | Yes | Yes | Yes | N/A where not meaningful | Yes for editable records |
| Money/Anomaly/Tax | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Graphs | Yes | Yes/filter-empty | Yes | Yes | Yes | Yes | Yes | N/A unless projection revision applies |
| Shared | Yes | N/A | Yes | neutral unavailable | N/A | Yes | Yes if supplied | N/A |

`403`, `404/not found`, `expired session` and a valid empty collection are separate fixtures and
must never share the same generic empty-state copy.

## 8. Global fixture and mock contract

### 8.1 Data origin

Use an explicit origin wrapper for every screen dataset:

```ts
type SurfaceData<T> = {
  origin: "synthetic_fixture";
  scenarioId: string;
  illustration: true;
  data: T;
};
```

During this phase there is no `origin: "live"` implementation. Preserve the future union boundary
in types, but do not add a live service adapter before approval.

### 8.2 Fixture safety rules

- All record identifiers start with `fixture:`.
- Every authenticated prototype route displays one global label:
  `DỮ LIỆU MINH HỌA — KHÔNG PHẢI DỮ LIỆU THỰC`.
- Financial, company, period, version, environment and approval values use bracketed illustration
  labels unless the scenario explicitly tests `unknown`.
- Buttons that would mutate real state begin with `Mô phỏng` in this phase.
- Mock mutations are reducer/service events with expected revision checks and an append-only local
  audit trail.
- No mock action may call `fetch`, `XMLHttpRequest`, `EventSource`, WebSocket or a backend client.
- Dates, IDs, latency and streaming chunks use deterministic clocks/seeds.
- Fixture collections for different scopes/roles are never merged to imply broader access.
- A permission-denied scenario contains no hidden unauthorized record names, counts or graph data.
- Logout or simulated session expiry clears fixture activation and selected private state.

### 8.3 Required scenario axes

Every page declares applicable values from these axes:

| Axis | Values |
|---|---|
| Role | accountant; chief accountant; finance manager; consultant; administrator |
| Capability | online-shaped fixture; offline local; limited capability; cloud blocked |
| Scope | fully unknown; partial; known illustration; changed; stale against task revision |
| Data | loading; ready; empty; recoverable error; forbidden; session expired |
| Evidence | none; user supplied; inferred; verified; missing; stale; conflicting |
| Mutation | idle; validating; success; validation failure; revision conflict; rejected |
| Viewport | 1440×900; 1024×768; 768×1024; 390×844 |
| Theme | light; dark; system-light; system-dark |
| Motion | normal; reduced motion |

## 9. Business scenario catalogue

Scenario IDs are stable review/test identifiers. Add fixtures against these IDs instead of
creating one-off component booleans.

### 9.1 Authentication and shell

| ID | Case | Expected business-safe outcome |
|---|---|---|
| AUTH-01 | SSO is available | SSO is primary; local password is shown only when permitted. |
| AUTH-02 | Password-only environment | Form validation is accessible; no fake SSO action. |
| AUTH-03 | Invalid credentials | Generic failure does not disclose account existence. |
| AUTH-04 | Protected deep link | After mock sign-in, return to the validated local target. |
| AUTH-05 | Unsafe/external `next` | Ignore target and return to `/`. |
| AUTH-06 | Session expires mid-task | Preserve a safe local return path; clear sensitive fixture state. |
| AUTH-07 | Non-admin identity | Admin nav, count and prefetch-shaped UI are absent. |
| AUTH-08 | Capability becomes limited | Show boundary; do not silently retain a cloud-confirmed presentation. |

### 9.2 Conversation

| ID | Case | Expected business-safe outcome |
|---|---|---|
| CHAT-01 | New Financial Close request | Recognize outcome but keep company/period/version unknown. |
| CHAT-02 | Ambiguous request | Ask one high-information clarification; no invented workflow facts. |
| CHAT-03 | Normal mock stream | Stable layout; status and chunks are readable; evidence opens in context. |
| CHAT-04 | User stops stream | UI becomes stopped; late fixture events are ignored; retry remains possible. |
| CHAT-05 | Recoverable stream error | Preserve received content, explain failure and offer retry. |
| CHAT-06 | Attachment upload pending/fails | Send is gated while processing; retry/remove are available. |
| CHAT-07 | Unsupported/oversized attachment | Explain accepted type/size without losing typed prompt. |
| CHAT-08 | Invoice creates a draft illustration | Clearly mark draft, evidence gaps and no ERP execution. |
| CHAT-09 | Citation/evidence selected | Desktop aside/mobile sheet preserves conversation position and focus. |
| CHAT-10 | No evidence | Helpful conditional response; never claim verification. |
| CHAT-11 | Stale/conflicting evidence | Block exact conclusion and expose safest next action. |
| CHAT-12 | Pause/resume/cancel | Pause preserves state; cancel disables composer but preserves history. |
| CHAT-13 | User switches real outcome | Increment task epoch and clear selected evidence from old task. |
| CHAT-14 | User corrects company/period | Increment revision and mark prior readiness for reassessment. |
| CHAT-15 | Edit/regenerate/truncate | Show impact boundary and deterministic local history replacement. |
| CHAT-16 | Like/dislike/report | Feedback UI has reversible state and report category/comment cases. |
| CHAT-17 | Share conversation | Preview read-only boundary; never imply recipient authorization. |
| CHAT-18 | Consultant profile correction | Profile affects presentation fixture only, never permission. |
| CHAT-19 | Loading/empty conversation | No fake answer or evidence counts. |
| CHAT-20 | Conversation forbidden/not found | Distinguish safe access failure from an empty conversation where possible. |
| CHAT-21 | Plan/status/tool progress | Show useful normalized progress without revealing chain-of-thought or sensitive arguments. |
| CHAT-22 | Tool result fails mid-stream | Keep prior content, identify failed operation and avoid a false successful conclusion. |
| CHAT-23 | Artifact announced/download unavailable | Keep a reviewable artifact reference; distinguish generated, downloadable and verified. |
| CHAT-24 | Duplicate/out-of-order events | Do not duplicate citations, drafts, artifacts, steps or answer content. |
| CHAT-25 | Create/copy/revoke share link | Make read-only scope visible; copy/revoke failure is recoverable. |
| CHAT-26 | Multiple mixed attachments | Per-file progress/error/removal; sending waits only for required processing. |
| CHAT-27 | Long Markdown/table/code/Mermaid-shaped answer | Safe rendering, horizontal containment, accessible alternative and no layout jump. |
| CHAT-28 | Grounded/cloud/clarification metadata | Labels reflect supplied event fields and never imply evidence strength not received. |
| CHAT-29 | Consultant state revision changes | Refresh or show stale state; do not overwrite a newer task status. |
| CHAT-30 | Long conversation and return navigation | Preserve reading position, selected evidence and composer focus where appropriate. |

### 9.2.1 Conversation history

| ID | Case | Expected business-safe outcome |
|---|---|---|
| HIST-01 | Normal list ordered by recent activity | Show title and date without inventing unread counts or ownership metadata. |
| HIST-02 | Loading/empty/error | Three distinct states; error offers retry and empty offers new conversation. |
| HIST-03 | Select a conversation | Navigate to stable `/c/:id`; selected state is visible on desktop and mobile. |
| HIST-04 | Delete confirm/cancel | Name the exact conversation; cancel preserves list and selection. |
| HIST-05 | Delete active conversation | Return safely to `/`; do not leave stale task/evidence state mounted. |
| HIST-06 | Rename valid/blank/too long | Validate locally; preserve previous title on simulated failure. |
| HIST-07 | Duplicate or fallback titles | Rows remain distinguishable using safe date/context, not private message previews by default. |
| HIST-08 | Large list/search/no result | Keyboard-usable filtering and a reset action; no fake pagination totals. |
| HIST-09 | Forbidden/deleted by another session | Neutral unavailable handling; remove stale entry without leaking owner data. |
| HIST-10 | Mobile open/back/restore | Conversation opens as primary view and back returns to prior list position. |

### 9.3 Financial Close Advisor

The eight required prerequisite groups are fixed:

1. Scope and reporting period.
2. Source documents posted.
3. Subledgers reconciled.
4. Applicable period processes.
5. Period-end entries.
6. Closing controls.
7. Report mappings and opening balances.
8. Reports and variance review.

| ID | Case | Expected business-safe outcome |
|---|---|---|
| CLOSE-01 | Fully unknown scope | No readiness conclusion; request company and accounting period. |
| CLOSE-02 | Partial assessment | Completed, in-progress and unassessed nodes expose reasons. |
| CLOSE-03 | Missing evidence | Dependent conclusion remains blocked or unconfirmed. |
| CLOSE-04 | Conflicting reconciliation | Conflict is prominent; next action requests resolution/evidence. |
| CLOSE-05 | Not applicable process | Requires an applicability reason, never a casual user toggle. |
| CLOSE-06 | All illustration nodes ready | State says illustration readiness, not real ERP readiness. |
| CLOSE-07 | Scope changes after ready | Prior ready nodes become `not_assessed` and revision changes. |
| CLOSE-08 | Stale evidence | Status explains staleness and required reassessment. |
| CLOSE-09 | Downstream node selected | Show prerequisites, blocking path, responsible role and safe action. |
| CLOSE-10 | Graph permission boundary | Hide unauthorized labels, counts, edges and aggregates. |
| CLOSE-11 | Mobile graph | Default to accessible list; graph/table remain explicitly selectable if usable. |
| CLOSE-12 | Graph search/filter no result | Clear empty result with reset action. |
| CLOSE-13 | Citation-to-node and node-to-chat | Preserve context and focus without fabricating a live link. |

### 9.4 Draft and approval

| ID | Case | Expected business-safe outcome |
|---|---|---|
| DRAFT-01 | Proposed/validating draft | Review actions disabled until validation reaches a reviewable state. |
| DRAFT-02 | Validation failed | Approval disabled; issues and missing checks are explicit. |
| DRAFT-03 | Ready for review with no gaps | Authorized reviewer can simulate approval at expected revision. |
| DRAFT-04 | Ready with missing checks | Approval remains disabled. |
| DRAFT-05 | Request changes | Non-empty note required; append audit event; increment revision. |
| DRAFT-06 | Reject | Non-empty reason required; append audit event; increment revision. |
| DRAFT-07 | Revision conflict | Reject stale action and show reload/compare guidance. |
| DRAFT-08 | Maker equals checker | Negative case blocks approval and explains role separation. |
| DRAFT-09 | Already approved | Read-only; label says not executed or verified. |
| DRAFT-10 | Export illustration | Only approved eligible drafts; result remains manual-action output. |
| DRAFT-11 | Non-approver | No approval queue details or mutation controls leak. |
| DRAFT-12 | Queue loading/empty/error/403 | Each state is distinct; 403 is never shown as empty. |
| DRAFT-13 | Multiple draft kinds | Journal, anomaly and tax projections show kind-specific fields without unsafe casting. |
| DRAFT-14 | Single CSV/XLSX export | Only eligible approved journal draft; filename and manual-action boundary are explicit. |
| DRAFT-15 | Mixed batch selection | Ineligible/rejected/non-journal rows cannot enter the export request-shaped fixture. |
| DRAFT-16 | Export failure/partial eligibility | No success download is claimed; retain valid selection and show correction. |
| DRAFT-17 | Approval/rejection service failure | Roll back optimistic state and keep expected revision/audit history unchanged. |
| DRAFT-18 | Unknown status or missing payload fields | Fail closed with unavailable detail; never reinterpret as pending/approved. |

### 9.5 Knowledge

| ID | Case | Expected business-safe outcome |
|---|---|---|
| KNOW-01 | List/search/filter | Scope and origin stay visible; no hidden cross-scope counts. |
| KNOW-02 | Empty scope | Offer relevant permitted action. |
| KNOW-03 | Upload illustration | Validate type/visibility; simulate progress/success/failure only. |
| KNOW-04 | Delete illustration | Confirm exact item and ownership; revision-aware local removal. |
| KNOW-05 | Ingestion pending/failed | Status and retry/help are explicit. |
| KNOW-06 | Draft/unapproved source | Never use approval wording that implies governed truth. |
| KNOW-07 | Superseded source | Link the relationship and warn against current use. |
| KNOW-08 | Conflicting sources | Show conflict and block a single authoritative conclusion. |
| KNOW-09 | Unknown metadata | Render `Không có từ API/Chưa xác định`, never invent owner/date/version. |
| KNOW-10 | File access forbidden | Do not preview content; explain permission boundary. |
| KNOW-11 | Deduplicated upload result | Explain existing source reuse without pretending a new governed document was created. |
| KNOW-12 | Disallowed visibility | Hide/disable unauthorized scope before file selection and explain required permission. |
| KNOW-13 | Multi-file partial success | Per-file result; successful fixtures remain while failed files can retry. |
| KNOW-14 | File preview/download failure | Keep metadata view, protect content and offer retry only when appropriate. |
| KNOW-15 | Large document collection | Responsive list/table behavior, stable filters and no invented total/count metadata. |

### 9.6 Admin, tools and shared surface

| ID | Case | Expected business-safe outcome |
|---|---|---|
| ADMIN-01 | Admin overview | Use only current-product-shaped fields; unknown health is unknown. |
| ADMIN-02 | Users/departments/permissions | Role/scope are understandable without exposing secrets. |
| ADMIN-03 | Usage/feedback/audit empty/error | Independent section boundaries; one failure does not fake all-empty. |
| ADMIN-04 | Non-admin deep link | Permission page; no admin content/counts are constructed. |
| ADMIN-05 | Create department | Required/duplicate/server-conflict-shaped cases; no success before local mock commit. |
| ADMIN-06 | Create user | Email/name/password validation; admin flag, departments and permissions reviewed together. |
| ADMIN-07 | Permission/department selection | Selected scope is readable by keyboard and remains visible before create. |
| ADMIN-08 | Invalid or duplicate user | Preserve entered safe fields; password is never echoed in error/audit copy. |
| ADMIN-09 | Reset user password | Explicit target confirmation, generated/entered password handling and no secret in audit UI. |
| ADMIN-10 | Edit/disable user-shaped contract case | Revision/conflict-aware mock; never silently broaden role or department scope. |
| ADMIN-11 | Current user password change handoff | Old/new/confirm validation and session implications; only show where permitted. |
| ADMIN-12 | Partial section failures | Users may load while usage/feedback fails; each section reports its own truth. |
| MONEY-01 | Invoice XML upload | Validate, simulate draft creation and show parse/review errors. |
| MONEY-02 | Pending/approved/rejected filters | Status remains distinct and stable across selection. |
| MONEY-03 | Batch export selection | Only eligible approved journal drafts are selectable. |
| MONEY-04 | Multiple XML files | Per-file progress and partial failure; no all-success summary when one fails. |
| MONEY-05 | Invalid/unsupported XML | No draft is created; show safe parse guidance without exposing raw sensitive XML. |
| MONEY-06 | Unbalanced or `needs_review` payload | Highlight validation flags and block approval as required. |
| MONEY-07 | Invoice/journal detail | Source invoice lines, debit/credit lines and totals are fixture-labelled and tabular. |
| MONEY-08 | Approve/reject draft | Same lifecycle rules as Approvals; reject reason required. |
| MONEY-09 | Export failure | Keep eligible selection and show no executed/imported claim. |
| MONEY-10 | Missing create/approve/export capability | Each affordance is independently hidden/disabled without hiding permitted read data. |
| ANOM-01 | Scan | Explicit simulation; result flags are drafts for investigation. |
| ANOM-02 | Review flag | Confirm investigation/reject with reason; no ERP correction claim. |
| ANOM-03 | Scan returns no findings | Explain scanned illustration scope; do not claim the real ledger is clean. |
| ANOM-04 | Mixed severity results | High/medium/low use text plus color and deterministic ordering. |
| ANOM-05 | Scan already running | Prevent duplicate action and expose cancellability only if actually modeled. |
| ANOM-06 | Scan partial/fails | Do not merge stale previous flags into the new result summary. |
| ANOM-07 | Stale anomaly draft | Require refresh/reassessment before reviewer action. |
| ANOM-08 | Read allowed, create/review denied | Preserve list where allowed and remove unauthorized actions. |
| TAX-01 | Reconcile | Explicit simulation; result is a recommendation draft. |
| TAX-02 | Review adjustment | Approval boundary remains separate from filing/execution. |
| TAX-03 | Required evidence absent | Guide to Knowledge/Chat; do not run or claim reconciliation. |
| TAX-04 | No mismatch found | State fixture scope and evidence limitations; no real compliance conclusion. |
| TAX-05 | Multiple adjustment drafts | Each shows basis, evidence, risk and separate review state. |
| TAX-06 | Reconcile partial/fails | Preserve inputs and provide retry; no success count. |
| TAX-07 | Stale tax evidence | Block recommendation approval until evidence refresh. |
| TAX-08 | Read allowed, create/review denied | Capability-specific affordances only; backend remains authoritative later. |
| KGRAPH-01 | Generic graph load | Visually and semantically distinct from Financial Close graph. |
| KGRAPH-02 | Open source/Ask AI | Local preview/handoff only; permission-safe unavailable state. |
| KGRAPH-03 | Toggle source groups | Hidden groups remove their nodes/edges without leaking counts in labels. |
| KGRAPH-04 | Similarity threshold | Explain threshold; deterministic fixture edges; no quality/authority implication. |
| KGRAPH-05 | Search/locate/no result | Select and focus matching source or provide resettable no-result state. |
| KGRAPH-06 | Zoom/fit/relayout/reload | Keyboard-labelled controls and reduced-motion-safe transitions. |
| KGRAPH-07 | Source file forbidden/missing | Inspector remains permission-safe; no content or path leakage. |
| KGRAPH-08 | Ask AI handoff | Starts a new local prompt with source label, not source content outside permission. |
| KGRAPH-09 | Large/complex graph | Accessible list/table alternative is complete, ordered and filter-equivalent. |
| KGRAPH-10 | Graph 403/empty/error/offline | Four distinct boundaries; no unauthorized node/edge/aggregate construction. |
| SHARE-01 | Valid token | Read-only conversation/evidence; no mutation controls. |
| SHARE-02 | Expired/revoked/invalid token | Neutral unavailable state; no record metadata leak. |
| SHARE-03 | Loading and recoverable error | Stable public shell, retry where safe, no protected navigation flash. |
| SHARE-04 | Long transcript/mobile | Readable messages, tables and code; no composer or account controls. |
| SHARE-05 | Evidence/artifact references | Show only fields supplied to the shared projection; unavailable links are inert. |
| SHARE-06 | Attempted mutation/deep action | No approval, feedback, edit, regenerate, download or private source action is constructed. |

### 9.7 Route and navigation failures

| ID | Case | Expected business-safe outcome |
|---|---|---|
| ROUTE-01 | Unknown path while signed out | Show public not-found/recovery or safe login path without protected-shell flash. |
| ROUTE-02 | Unknown path while signed in | Offer home/history recovery; no unrelated data is prefetched for the error page. |
| ROUTE-03 | Malformed conversation/fixture ID | Reject locally and show unavailable; never build a future API request with `fixture:`. |
| ROUTE-04 | Classic alias | Preserve query/hash only when safe and route to the documented candidate page. |
| ROUTE-05 | Hidden/disabled module deep link | Apply the permission/availability boundary; do not redirect deceptively to empty content. |

## 10. Work package details

### UI-00 — tracker, scope freeze and inventory

- [x] Record UI-first owner direction and integration hold.
- [x] Record repository baseline and protect `frontend-react`.
- [x] Inventory current Figma screens and classic compatibility surfaces.
- [x] Define canonical page, role, state and business-scenario matrices.
- [x] Define owner approval gate and post-approval lock.
- [x] Owner accepts this tracker as the UI-first source of truth.

Exit: owner accepts scope/order; change status to `APPROVED`; start UI-01 only.

### UI-01 — prototype foundation and complete route shell

- [x] Keep React 19, Vite 8, Tailwind 4 and pnpm lockfile unless owner approves a change.
- [x] Add React Router with all section 7 routes backed by fixtures.
- [x] Create route-level error/not-found boundaries.
- [x] Separate design tokens/primitives from page compositions.
- [x] Add Light/Dark/System with flash-free initialization.
- [x] Keep expanded, compact, tablet and mobile navigation behavior.
- [x] Make role/capability/fixture/state selectors URL-addressable in QA mode.
- [x] Add deterministic clock, IDs and mock stream scheduler.
- [x] Add typecheck, unit/component, accessibility and visual-test scripts.
- [x] Add a guard/test that fails if a fixture service makes a network request.
- [x] Preserve Figma Make portability or record an owner decision changing authority.

Exit: every page route renders a safe placeholder or page; clean typecheck/test/build pass.

### UI-02 — sign-in and protected-navigation mock UX

- [x] Implement AUTH-01..AUTH-08.
- [x] Validate safe `next` handling in the local router.
- [x] Design account/session-expiry/re-authentication states.
- [x] Verify non-admin navigation at every viewport.
- [x] Make clear that authentication is simulated.

Exit: review URLs for all auth cases; keyboard and validation checks pass.

### UI-03 — conversation surfaces

- [x] Complete new conversation and dedicated history experience.
- [x] Implement CHAT-01..CHAT-30, HIST-01..HIST-10 and SSE-01..SSE-18 with deterministic fixture services.
- [x] Preserve outcome, prerequisite, evidence, next-action and uncertainty answer structure.
- [x] Complete attachments, invoice draft, stop/retry and late-event suppression UX.
- [x] Complete evidence aside/mobile sheet and focus restoration.
- [x] Complete edit/regenerate/truncate, feedback/report and share preview UX.
- [x] Cover task pause/resume/cancel/switch and scope correction.
- [x] Never expose chain-of-thought or mechanical private reasoning.

Exit: owner can traverse every conversation case without a backend.

### UI-04 — Financial Close and evidence graph

- [x] Implement CLOSE-01..CLOSE-13.
- [x] Preserve exactly eight governed prerequisite groups.
- [x] Expose reason, evidence, missing evidence, responsible role and safe next action per node.
- [x] Implement graph/list/table parity, search, filters, inspector, fit/reset and no-result state.
- [x] Implement accessible logical-order keyboard traversal and mobile list default.
- [x] Verify no unexplained percentage, score, donut or readiness claim appears.

Exit: all readiness statuses and dependency cases are reviewable at four viewports.

### UI-05 — drafts and approval

- [x] Implement DRAFT-01..DRAFT-18.
- [x] Build queue filters, selection, detail and mobile review flow.
- [x] Preserve before/after, purpose, scope, evidence, risk, gaps and audit trail.
- [x] Make transitions expected-revision aware and fail closed.
- [x] Keep approved/exported/executed/verified visually and linguistically distinct.

Exit: negative maker-checker, missing-check and stale-revision cases visibly block action.

### UI-06 — Knowledge library

- [x] Implement KNOW-01..KNOW-15.
- [x] Cover personal/department/global-shaped fixture scopes without mixing them.
- [x] Design upload, delete, file detail/preview and ingestion-state simulation.
- [x] Show owner/version/effective/approval/visibility/traceability only when supplied.
- [x] Cover superseded/conflicting documents and permission-safe unavailable states.

Exit: governance meaning remains correct across list, detail and mutations.

### UI-07 — Administration and audit

- [x] Implement ADMIN-01..ADMIN-12.
- [x] Cover users, departments, permissions, usage and quality-feedback layouts.
- [x] Cover audit, runtime policy, controlled egress and service-health read-only views.
- [x] Keep independent loading/error/empty boundaries per section.
- [x] Remove or label any field not supplied by current platform contracts.

Exit: non-admin case constructs no admin data; admin screens are responsive and understandable.

### UI-08 — operational parity pages

- [x] Implement MONEY-01..MONEY-10.
- [x] Implement ANOM-01..ANOM-08.
- [x] Implement TAX-01..TAX-08.
- [x] Implement KGRAPH-01..KGRAPH-10.
- [x] Lazy-load these page modules in the prototype router.
- [x] Keep each output draft/recommendation-based and never imply ERP execution.

Exit: owner can approve, omit or request changes for each parity page independently.

### UI-09 — shared surface and route completion

- [x] Implement SHARE-01..SHARE-06 and ROUTE-01..ROUTE-05.
- [x] Implement local not-found and safe recovery states.
- [x] Prototype compatibility aliases without coupling them to backend serving.
- [x] Verify shared/read-only UI has no mutation affordance.

Exit: every target/alias route has a documented deterministic result.

### UI-10 — cross-route quality matrix

- [x] Apply all relevant axes from section 8.3 to every page.
- [x] Complete loading, ready, empty, error, 403, expiry, offline and limited states.
- [x] Add stale/conflict/revision states where business meaning requires them.
- [x] Run 1440×900, 1024×768, 768×1024 and 390×844 visual matrix.
- [x] Run light/dark/system and reduced-motion matrix.
- [x] Run keyboard-only flows, focus trap/restore, 200% zoom and 44px mobile targets.
- [x] Run automated accessibility checks on every route and major state.
- [x] Verify Vietnamese-first copy and tabular numerals.
- [x] Verify no generic AI gradients, glassmorphism, decorative financial KPIs or fake charts.
- [x] Verify official logo and `//` motif rules.

Exit: no P0 route/case is missing or fails a required quality matrix.

### UI-11 — owner review pack and FE-only gate

- [x] Produce a route index with direct QA URLs for every P0/P1 case.
- [x] Produce representative screenshots for four viewports in light and dark.
- [x] Produce a role/capability navigation comparison.
- [x] Produce a business-invariant review for Conversation, Close, Draft and Knowledge.
- [x] List deliberate omissions and unsupported backend data separately.
- [x] Record typecheck/test/a11y/visual/build results.
- [x] Demonstrate zero real auth/API/SSE/mutation traffic.
- [x] Request explicit owner decision from section 16.

Exit: owner selects `APPROVED`, `CHANGES_REQUESTED` or `REJECTED`.

## 11. Visual and interaction acceptance rules

- Direction remains `Assured Operations — Quản trị chắc chắn, có bằng chứng`.
- Official BRAVO green leads; accessible teal is used for interaction.
- Orange is attention/pending, red is confirmed conflict/blocking error, and status always has text.
- Typography is operational and restrained; financial/date/version values use tabular numerals.
- Desktop answer width remains readable; evidence detail is an aside, not a second dashboard.
- Mobile keeps one primary task per view and defaults graph content to accessible list form.
- Streaming/mock progress never shifts the page horizontally or causes unstable navigation.
- Use subtle borders before shadows; avoid nested cards and pill-heavy layouts.
- The official logo is not recolored, distorted, rotated, shadowed or merged with product text.
- `//` is used only for evidence/progress/relationship meaning.
- Focus is visible; dialogs/sheets trap focus and restore it to the trigger.
- Every icon-only action has an accessible name and every error states a corrective action.

## 12. Verification commands and evidence

Use actual scripts after UI-01 creates them; update this section if names change.

```powershell
Set-Location FigmaMake_UI
pnpm.cmd install --frozen-lockfile
pnpm.cmd run typecheck
pnpm.cmd run test
pnpm.cmd run test:a11y
pnpm.cmd run test:visual
pnpm.cmd run build
```

Repository hygiene:

```powershell
git status --short
git diff --check
git diff --stat -- FigmaMake_UI
git diff -- frontend-react
```

The final command must produce no changes. Do not stage or commit user-owned work unless separately
requested.

### Evidence log

| Date | Package | Command/review | Result | Evidence/artifact | Notes |
|---|---|---|---|---|---|
| 2026-07-20 | Prototype baseline | TypeScript + production build | PASS | `DESIGN-QA-RESULTS.md` | Historical baseline; not UI-first acceptance |
| 2026-07-21 | UI-00 | Context/repo inventory and route/case parity cross-check | PASS | this tracker; 171 unique defined case IDs | No product code changed |
| 2026-07-21 | UI-01..UI-09 | Fixture router, deterministic services, page/case implementation and guarded actions | PASS | `src/`; `/review?qa=1`; 171 unique case URLs | FE-only; no live integration |
| 2026-07-21 | UI-10 | Typecheck, 3 test files/7 tests, axe smoke, visual matrix manifest and production build | PASS | package scripts; `review-artifacts/README.md` | Pixel-diff baselines deliberately omitted |
| 2026-07-21 | UI-11 | Four-viewport screenshot pack and owner-gate review | READY_FOR_REVIEW | `review-artifacts/` | Section 16 remains `NOT_REVIEWED` |

## 13. Stop conditions

Stop implementation and request owner direction when:

- a requested page or case materially conflicts with BRAVO business invariants;
- a design decision would remove a current capability rather than present it differently;
- a page requires inventing exact financial, schema, version, authorization or governance data;
- a mock and future live projection cannot be kept structurally distinguishable;
- work would require a backend, prompt, retrieval, migration, Docker, CI or classic-frontend change;
- a security-sensitive behavior cannot be represented without implying frontend enforcement;
- a dependency breaks offline production-build requirements or Figma Make portability;
- more than one materially different visual/product direction is plausible and the choice would
  cause significant rework;
- UI-11 is ready and owner approval has not yet been recorded.

Do not stop for ordinary implementation details that can be safely resolved within these contracts.

## 14. Owner decision protocol

When owner input is required, use an option box if the active Codex surface supports it. Ask one
short decision at a time with two or three mutually exclusive choices:

- put the recommended option first and label it `(Recommended)`;
- explain the visible scope/trade-off in one sentence per option;
- do not include a generic `Other` option when the UI adds it automatically;
- do not continue the blocked package until the owner responds;
- record the answer in section 15 before implementation resumes.

Do not request owner input for internal file naming, component decomposition or other reversible
technical details. Owner confirmation is required for scope omission, visual-direction changes,
business-behavior changes, Figma portability changes, and the final integration gate.

## 15. Decision log

| ID | Date | Decision needed/result | Status | Impact |
|---|---|---|---|---|
| DEC-001 | 2026-07-21 | Use UI-first fixture development before auth/API/SSE integration | `OWNER_DIRECTED` | FM-01 is held until UI-11 approval |
| DEC-002 | 2026-07-21 | Accept this tracker and start UI-01 | `OWNER_DIRECTED` | UI-first FE implementation authorized; integration approval not granted |

## 16. FE-only owner acceptance gate

This is the only valid gate into integration planning.

Current decision: `NOT_REVIEWED`

Allowed recorded outcomes:

| Outcome | Meaning | Next action |
|---|---|---|
| `APPROVED` | Visual system, pages, cases and FE behavior are accepted for integration | Unlock INT-00; re-plan FM-01 against accepted UI |
| `CHANGES_REQUESTED` | Direction is accepted but named corrections remain | Mark affected packages and UI-11 accordingly; remain FE-only |
| `REJECTED` | Candidate direction is not accepted | Stop and request a new owner direction; do not integrate |

An approval must include date and owner statement. Passing tests, screenshots, lack of feedback or
an AI assessment never substitutes for owner approval.

```text
Owner decision: NOT_REVIEWED
Decision date: —
Approved scope/version: —
Required follow-up: —
```

## 17. Post-approval integration hold

INT-00 remains `LOCKED` until section 16 says `APPROVED`.

When unlocked, do not integrate immediately. First compare the accepted fixture UI with plan 09
and write an integration delta covering:

1. React Router and protected route mapping.
2. API client, normalized errors and DTO mapping.
3. Existing auth/password/OIDC and `/api/me` behavior.
4. Exact POST+SSE event grammar, stop and late-event suppression.
5. Capability mirror versus backend authorization.
6. Live-versus-fixture service split and `fixture:` rejection.
7. Current API fields versus UI fields that must remain unavailable.
8. Contract/unit/E2E/security/a11y/visual gates.
9. Staging, immutable bundle, rollback and WP-00A release containment.

Integration must adapt the accepted frontend to existing contracts. Any backend gap triggers the
stop condition and a separate owner decision.

## 18. Current handoff

```text
Objective:
Complete FigmaMake_UI as a fixture-driven, business-correct frontend for owner review before any
real auth/API/SSE integration.

Current status:
- UI-00 is APPROVED by the owner's instruction to implement this tracker.
- UI-01..UI-10 are implemented against deterministic fixture routes and are READY_FOR_REVIEW.
- UI-11 review pack is READY_FOR_REVIEW; section 16 remains NOT_REVIEWED.
- INT-00 and FM-01..FM-08 implementation are locked until the FE-only owner gate is APPROVED.
- frontend-react is a read-only classic comparator/rollback source.

Next exact action:
1. Owner reviews `/review?qa=1` and the artifacts in `review-artifacts/`.
2. Owner records APPROVED, CHANGES_REQUESTED or REJECTED in section 16.
3. No implementation resumes until that decision is recorded.

Do not:
- connect real auth, API or SSE;
- start FM-01;
- edit frontend-react/backend/prompts/retrieval/migrations;
- invent exact BRAVO/financial/governance facts;
- confuse a fixture action with authorization, execution or verification.

Verification before the next handoff:
- candidate typecheck/test/a11y/visual/build passed;
- 171 case IDs are unique and route-addressable;
- four representative viewport screenshots were captured;
- frontend-react remains unchanged;
- dashboard, checklist, evidence log and this handoff are updated.
```
