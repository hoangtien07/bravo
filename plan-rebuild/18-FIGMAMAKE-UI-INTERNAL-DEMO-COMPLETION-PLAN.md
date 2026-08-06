# FigmaMake UI V2 internal-demo completion plan

Status: `TECHNICAL DEMO-COMPLETE — READY FOR OWNER EVALUATION; EXTERNAL GATES REMAIN OPEN`

Date: 2026-08-03

Execution target: `FigmaMake_UI/`

Product boundary: `BRAVO Accounting Intelligence — Knowledge Chat + Accounting Operations Hub`

Release claim: `LOCAL SYNTHETIC INTERNAL DEMO ONLY`

## 1. Owner intent and completion boundary

The owner requires one coherent FigmaMake candidate that can be started locally and demonstrated
end to end. It must no longer present fixture-backed or non-functional screens as if they were live.
The internal demo has two separately governed modules in one trusted shell:

1. **Knowledge Chat** — server-backed conversation history, authenticated POST-SSE turns, grounded
   evidence/citations, attachments or governed sources where supported, feedback and read-only
   sharing.
2. **Accounting Operations Hub (`Công việc AI`)** — one inbox and three durable synthetic cases:
   Bank Reconciliation, Voucher Evidence & Accounting Review, and Period Close Readiness, including
   maker creation/checks, independent reviewer review, and non-executing artifact export.

For this plan, **complete** means `demo-complete`, not production-ready. A demo-complete route:

- uses the local FastAPI contract or an explicitly activated QA fixture provider;
- has no frontend-hard-coded business conclusion, evidence result, financial value or permission;
- has no dead primary action;
- distinguishes live data, server-served frozen synthetic evidence, QA fixture and unavailable data;
- exposes loading, empty, denied, conflict, offline and recoverable-error behavior;
- preserves authorization, RLS, evidence lineage, revision/idempotency and maker-checker boundaries.

This plan does not close the blind SME, conversation-quality A/B/C/D, real-data, pilot, recovery,
deployment or production gates. Those remain governed by Plans 10, 12 and 15 plus ADR-0032/0033.

## 2. Authority and relationship to earlier plans

- Plan 17 remains the execution record for the three AccountingCase frontend packages. Its
  FEV2-10 handoff is complete through the fresh live two-identity walkthrough and bundle/rollback
  evidence recorded on 2026-08-03; it does not imply an owner acceptance or release authority.
- This Plan 18 is the completion umbrella for the **whole internal-demo product shell**. It adds the
  live Knowledge Chat cutover, route containment, demo identities, packaging and rehearsal needed
  to make the FigmaMake candidate coherent.
- Plan 09 is historical cutover input. This plan does not revive broad parity with legacy Money
  Engine, Tax, Anomaly, Knowledge Graph, generic draft queue or Administration.
- `frontend-react/` remains a read-only behavioral comparator and rollback source. New product work
  belongs in `FigmaMake_UI/`.

Precedence remains: running code/tests/migrations and runtime evidence > this plan > historical
progress claims. No plan checkbox is evidence by itself.

### 2.1 Execution reconciliation (2026-08-03)

The work-package status table below is the Plan 18 completion record. Detailed unchecked task
lists are retained as the frozen pre-execution audit ledger; they are not a substitute for the
runtime and browser evidence indexed in `evidence/v2/DEMO18-FINAL-PACKET-2026-08-03.md`.

## 3. Recorded starting truth

### 3.1 Repository and runtime baseline

| Item | Observed truth on 2026-08-03 | Consequence |
|---|---|---|
| Git commit | `c41255635bee7e594e4b867cf26f5691b98097cc` on `codex/v2-financial-close-core` | The admitted remediation worktree is dirty; preserve all unrelated changes |
| Migration source head | `0020_case_v2_audit` | Runtime migration state must still be verified from the demo database before rehearsal |
| Candidate package | React 19, React Router 7, Vite 8, Vitest 4, Playwright | Reuse the current toolchain; no framework migration |
| Local API | Docker FastAPI can start on `127.0.0.1:8000`; runtime fixture copy was added to the image | Rebuild is required when the Dockerfile/core fixture set changes |
| Local database | Host port may need `BRAVO_POSTGRES_HOST_PORT=55432` because `5432` is occupied | Demo launcher must resolve this deterministically |
| Auth | Password login and `/api/me` work; OIDC is disabled in the local demo | Password login is the supported rehearsal path |
| FE gates | Plan 17 records typecheck/build, 17 Vitest tests and two Playwright QA/protected-route tests passing | Re-run; prior evidence does not cover live Knowledge Chat or two identities |

The host currently lacks a directly callable Alembic CLI, so migration runtime truth must be
collected inside the API/container environment. Do not infer applied DB revision from the filename.

### 3.2 Route and data-source audit

| Surface | Current source | Classification | Required disposition |
|---|---|---|---|
| `/login` | `/api/auth/config`, `/api/auth/login`, `/api/me` outside QA | `LIVE` | Retain and harden timeout/error copy |
| `/work`, `/work/new/:caseType`, `/work/cases/:caseId` | V2 AccountingCase API | `LIVE/PARTIAL` | Retain, integrate into final shell, close two-user handoff |
| `/`, `/c/:id` | `AppContext`, `fixtures/scenarios.ts`, `fixture:*` navigation | `MOCK` | Replace with typed live conversation services outside `?qa=1` |
| `/conversations` | prototype constant list | `MOCK` | Replace with owner-scoped server history |
| `/shared/:token` | fixture token projection | `MOCK` | Implement the public read-only API contract or hide Share until complete |
| Evidence rail on chat | illustrative cards and placeholder sources | `MOCK` | Derive from returned citations/evidence references; truthful empty state otherwise |
| `/knowledge` | prototype/AppContext knowledge data | `MOCK/PARTIAL` | Implement bounded governed-source view needed by Chat, or hide from primary demo nav |
| `/approvals`, `/financial-close/graph` | legacy/prototype state | `OUT OF V2 DEMO` | Remove from live primary navigation; keep only explicit QA/reference access if needed |
| Money Engine, Anomaly, Tax, Knowledge Graph, QA index | fixture registry/prototype pages | `LEGACY/QA` | Never display in normal demo navigation; keep under `?qa=1` only |
| `/admin` | prototype state, auth-gated label only | `OUT OF V2 DEMO` | Hide until a separate live admin acceptance plan exists |

### 3.3 Existing backend contracts available for reuse

Knowledge Chat does not require a newly invented backend:

- `GET /api/conversations`
- `GET /api/conversations/{conversation_id}`
- `POST /api/chat/{conversation_id}/messages` using `fetch` + `ReadableStream` SSE with bearer auth
- rename, delete and truncate conversation endpoints
- share/unshare and unauthenticated read-only shared conversation endpoints
- message feedback endpoint
- attachment upload/status/delete endpoints
- source APIs and owner/department authorization where used
- existing SSE events: `id`, `plan`, `plan_update`, `source`, `attachments`, `status`, `step`,
  `tool_call`, `tool_result`, `artifact`, `draft`, `answer`, `done`, `error`, `ping`

The classic frontend is an implementation reference for the stream grammar only. Do not copy its
visual design or mutate its source.

### 3.4 Confirmed gaps

1. Normal conversation routes still route to `fixture:*` and can disable network entirely.
2. The shell exposes legacy menus that appear functional but are not part of the V2 demo contract.
3. `scripts/seed_demo.py` does not grant maker/reviewer `accounting_case:*` capabilities.
4. There is no attested live maker → reviewer → export lifecycle for all three cases.
5. There is no live Knowledge Chat browser E2E against the local API/SSE contract.
6. Existing visual tests cover QA/protected-route snapshots, not the final two-module product.
7. The earlier approved design specification remains Financial-Close-centric and must be reconciled
   with the accepted two-module product architecture.

## 4. Frozen product information architecture

### 4.1 Normal demo navigation

```text
BRAVO Accounting Intelligence
├── Knowledge Chat
│   ├── Bắt đầu hội thoại
│   ├── Hội thoại gần đây
│   └── Nguồn tri thức (only when live and authorized)
└── Công việc AI
    ├── Hộp công việc
    ├── Bank Reconciliation
    ├── Voucher Evidence Review
    └── Period Close Readiness
```

Primary navigation is capability-filtered before any protected label, count or prefetch is exposed.
QA routes remain directly addressable only with explicit `?qa=1`; they never appear in normal
navigation or share live providers.

### 4.2 Route target

| Route | Job | Required provider |
|---|---|---|
| `/` | Start a live conversation and show recent server conversations | Conversation API |
| `/c/:conversationId` | Read/send/stop a live conversation with contextual evidence rail | Conversation + SSE APIs |
| `/conversations` | Search/manage owner-scoped conversation history | Conversation API |
| `/shared/:token` | Read-only shared transcript with no protected shell leakage | Shared API |
| `/knowledge` | Governed sources used by Knowledge Chat, if acceptance contract passes | Source API |
| `/work` | Authorized Accounting Work inbox | AccountingCase API |
| `/work/new/:caseType` | Create one enabled synthetic case | AccountingCase API |
| `/work/cases/:caseId` | Evidence/check/review/export workspace | AccountingCase API |

Legacy aliases may redirect to a truthful target but must not preserve a fake live surface.

## 5. Frozen design direction

### 5.1 Subject, audience and single job

Subject: evidence-backed accounting investigation and review.

Audience: Vietnamese accountants, chief accountants and authorized internal reviewers.

Single job of the shell: make the current scope, evidence strength and next authorized action
understandable without implying that BRAVO has executed an accounting mutation.

### 5.2 Compact token system

| Token | Hex | Use |
|---|---|---|
| `bravo-green` | `#00A88D` | official logo and verified brand moments |
| `action-teal` | `#006B5D` | primary controls, links and focus |
| `soft-evidence` | `#E8F7F4` | selected/verified evidence relationship |
| `work-canvas` | `#F6F9F8` | quiet accounting workspace |
| `ledger-ink` | `#1F2927` | body and decision text |
| `attention-amber` | `#FBAF3F` | missing/pending evidence only |
| `conflict-red` | `#B42318` | confirmed conflict or blocking failure only |

Typography stays offline-safe and operational:

- display/section role: `Segoe UI Variable Display`, semibold, restrained;
- body/control role: `Segoe UI`/system UI;
- hash, revision, rule and financial-data utility role: `Cascadia Mono` with tabular numerals,
  falling back to the system monospace stack.

No decorative webfont download is permitted for the local/offline candidate.

### 5.3 Layout concept

Desktop uses a governed three-zone workspace, not three unrelated card columns:

```text
+--------------------+-------------------------------------------+----------------------+
| Product + module   | Scope bar: company / branch / period      | Evidence summary     |
| navigation         +-------------------------------------------+----------------------+
|                    |                                           | // claim relationship|
| recent threads or  | Conversation OR AccountingCase workspace | source / rule / hash |
| work filters       |                                           | status / next action |
|                    |                                           |                      |
| identity + runtime | anchored composer or lifecycle actions    | contextual inspector |
+--------------------+-------------------------------------------+----------------------+
```

- At 1024px the navigation collapses and the evidence rail remains available as a controlled
  inspector.
- At tablet/mobile, navigation and evidence become separate focus-managed drawers; the central job
  remains usable at 200% zoom.
- The evidence panel is contextual. It must not show illustrative cards unrelated to the selected
  message, finding or result.

### 5.4 Signature and self-critique

The single memorable element is the paired 29-degree `// Evidence Rail`. It connects a selected
claim or finding to source, scope, rule/hash and review state. It may advance once when evidence is
verified and must respect reduced motion.

The earlier prototype overuses `//` as avatar/decoration and relies on nested bordered cards. The
implementation pass must remove decorative repetitions and spend the signature only on evidence
lineage. Borders encode scope/state separation; they are not card decoration. No gradient, glass,
generic AI sparkle, fake KPI or unexplained readiness percentage is allowed.

## 6. Implementation architecture

Target structure; exact splitting may change only when tests prove a simpler boundary:

```text
FigmaMake_UI/src/
  app/                       router, live providers, protected shell, error boundaries
  api/
    auth.ts
    http.ts
    conversations.ts         strict CRUD/shared DTOs
    conversationStream.ts    POST-SSE parser and event decoder
    attachments.ts
    sources.ts
    accountingCases.ts
  auth/                      existing candidate-scoped session
  capabilities/              presentation mirrors; server remains authoritative
  conversation/
    ConversationHome.tsx
    ConversationHistory.tsx
    ConversationWorkspace.tsx
    ConversationComposer.tsx
    MessageTranscript.tsx
    ConversationEvidenceRail.tsx
    SharedConversation.tsx
  knowledge/                 bounded live source browser/picker
  accounting-work/           existing three-case implementation, reshaped into final shell
  design/                    tokens, shell primitives, Evidence Rail, hard-state components
  fixtures/                  QA only, explicit zero-network boundary
  test/                      unit, DTO, SSE, capability, a11y and visual coverage
```

Rules:

- Components never call `fetch` directly.
- API decoders reject malformed success payloads instead of guessing fields.
- Live and QA fixture providers cannot return a mixed collection.
- UUIDs are generated client-side only where the current server contract expects a new conversation
  ID; `fixture:*` identifiers are rejected before any live request.
- The browser does not calculate accounting conclusions or reconstruct hidden evidence.
- Streaming state is ephemeral; completed messages are reconciled with the durable conversation.
- No chain-of-thought is rendered. Status/tool summaries are shown only when already safe and useful
  in the server event contract.

## 7. Work packages and dependency order

| WP | Work package | Status | Depends on |
|---|---|---|---|
| DEMO18-00 | Baseline, truth audit and authority reconciliation | `COMPLETE — DEMO18-00 baseline` | owner scope confirmation |
| DEMO18-01 | Route containment and final product shell | `COMPLETE — normal live shell/browser evidence` | DEMO18-00 |
| DEMO18-02 | Knowledge Chat contract and POST-SSE foundation | `COMPLETE — contract, parser and live SSE evidence` | DEMO18-00 |
| DEMO18-03 | Live conversation home/history/workspace | `COMPLETE — durable live browser evidence` | DEMO18-01..02 |
| DEMO18-04 | Contextual evidence, sources, attachments and share | `COMPLETE — citation/attachment/share browser evidence` | DEMO18-03 |
| DEMO18-05 | Accounting Operations final-shell integration | `COMPLETE — three-case browser evidence` | DEMO18-01 |
| DEMO18-06 | Demo identities, permissions and deterministic reset | `COMPLETE — identity/API/browser evidence` | DEMO18-05 |
| DEMO18-07 | Security, hard states, a11y and responsive completion | `COMPLETE — probes, axe, keyboard and visual matrix` | DEMO18-03..06 |
| DEMO18-08 | Live local API/browser verification | `COMPLETE — DEMO18-08 runtime/browser` | DEMO18-07 |
| DEMO18-09 | Packaging, rehearsal and internal-demo evidence | `COMPLETE — DEMO18-09 and final packet` | DEMO18-08 |
| DEMO18-10 | Plan 17/18 closure record | `COMPLETE — evidence-indexed; owner acceptance pending` | DEMO18-09 |

Only one WP may be `IN_PROGRESS`. A package becomes `COMPLETE` only when its named exit evidence is
preserved; code presence or a visual screenshot alone is insufficient.

### DEMO18-00 — baseline, truth audit and authority reconciliation

- [ ] Preserve `git status --short`, baseline commit, branch and diff scope without cleaning the
  user's worktree.
- [ ] Verify the applied Alembic revision from the running demo database/container.
- [ ] Re-run current FigmaMake typecheck/tests/build before new changes.
- [ ] Normalize Plan 17's summary table, detailed checklists and FEV2 status evidence so they do not
  contradict each other.
- [ ] Freeze live/mock/QA/hidden route matrix and the exact endpoint subset for this plan.
- [ ] Record a must-not-claim list for Knowledge Chat and the three cases.

Exit evidence: baseline report, runtime migration output, green pre-change gate log, route/source
matrix and explicit list of unrelated dirty files preserved.

### DEMO18-01 — route containment and final product shell

- [ ] Refactor route/provider ownership so normal routes cannot consume `AppContext` fixture data.
- [ ] Limit normal navigation to Knowledge Chat, `Công việc AI`, and live governed sources when
  authorized.
- [ ] Hide QA index, Money Engine, Anomaly, Tax, generic graph, generic approvals and prototype Admin
  from normal navigation and prefetch.
- [ ] Keep QA activation explicit with `?qa=1`, a permanent banner and zero-network live-service
  guard.
- [ ] Implement the scope bar from server identity/context only; render `Chưa xác định` rather than
  invent company, branch, period or BRAVO version.
- [ ] Implement desktop collapsed navigation, tablet/mobile drawer, skip link, focus return and
  reduced-motion behavior.
- [ ] Replace prototype-oriented error copy such as “reload fixture” on live routes.

Exit: every normal nav item lands on a server-backed or truthfully unavailable route; no fixture ID,
fixture business content or hidden-route label appears in a normal authenticated DOM/network trace.

### DEMO18-02 — Knowledge Chat contract and POST-SSE foundation

- [ ] Freeze `contracts/KNOWLEDGE-CHAT-API-V1.md` from the current FastAPI routes and representative
  success/error/SSE payloads.
- [ ] Implement strict DTO decoders for conversation summary/detail/message/shared transcript.
- [ ] Implement an authenticated conversation API using the candidate token namespace and common
  `401/403/404/409/422/429/5xx/network` error grammar.
- [ ] Implement a POST + `ReadableStream` SSE parser supporting CRLF, split chunks, comments,
  multiple records, malformed-record isolation and abort.
- [ ] Decode the complete known event union and fail visibly on unsupported terminal behavior.
- [ ] Preserve `busy`, cancel/interrupted, incomplete stream and reconnect semantics without
  optimistic durable success.
- [ ] Add fixture-ID rejection and no-token/no-prefetch tests.

Exit: contract and stream parser tests pass against frozen backend examples, including chunk
boundaries, abort, error event, terminal `done`, citations and message IDs.

### DEMO18-03 — live conversation home, history and workspace

- [ ] Replace `/` fixture action with a real new-conversation ID and first POST-SSE turn.
- [ ] Load recent conversations from `GET /api/conversations`; show separate empty/error/denied
  states and never swallow failures into an empty list.
- [ ] Replace `/conversations` constants with owner-scoped history, open, rename and delete flows.
- [ ] Load `/c/:conversationId` from server and return scoped `404` without existence leakage.
- [ ] Implement optimistic user bubble + streaming assistant placeholder, then reconcile durable
  IDs/content on `done` or refetch.
- [ ] Support stop generation, same-conversation busy response, retry as new intent and safe reload.
- [ ] Implement edit/regenerate through the existing truncate contract with explicit destructive
  confirmation and retained audit semantics.
- [ ] Preserve scroll position, avoid layout shift and provide live-region updates without reading
  every streamed token to assistive technology.

Exit: login → new conversation → streamed answer → reload durable transcript → rename/delete works
against the local API; failure/abort leaves no false completed answer.

### DEMO18-04 — contextual evidence, sources, attachments and sharing

- [ ] Map final `citations` and safe source events to a contextual Evidence Rail; selecting a claim
  or citation focuses its source without moving the transcript.
- [ ] Show a truthful `Không có bằng chứng được trả về` state when the contract supplies no
  citations. Never synthesize source title, company, period, page or verification state.
- [ ] Distinguish grounded/ungrounded, locally handled/routed-cloud where returned, and clarify/
  abstain behavior in user language without overstating verification.
- [ ] Implement attachment upload/readiness/removal and prevent send until selected uploads are
  ready; preserve owner scoping and server limits.
- [ ] Implement governed source selection/pinning from the source API. If required metadata is not
  available, mark it unavailable rather than infer it.
- [ ] Implement like/dislike/report feedback only after the server returns the durable message ID.
- [ ] Implement share/unshare and live `/shared/:token` read-only transcript; shared view must not
  expose the authenticated shell, protected metadata or mutation controls.
- [ ] Keep deep-research artifacts out of the demo primary path unless artifact open/download is
  verified end to end.

Exit: citation selection, no-citation truth state, attachment turn, feedback and read-only share pass
contract and browser tests. No placeholder evidence label remains on a live route.

### DEMO18-05 — Accounting Operations final-shell integration

- [ ] Move the existing `/work` inbox and three case screens into the same final scope/evidence shell
  without changing server-owned calculations or state transitions.
- [ ] Make the AccountingCase Evidence Rail use the same visual grammar as Chat while retaining
  snapshot, lineage, rule, hash, revision and supersession semantics.
- [ ] Verify all state-based actions against current server responses for Bank, Voucher and Period.
- [ ] Keep Bank as the deep demonstrator and Voucher/Period as bounded shared-core cases.
- [ ] Remove or QA-isolate remaining Financial Close prototype projections and aliases that can be
  confused with Period Close Readiness.
- [ ] Verify `403` and scoped `404` clear protected local projections; verify `409` refetch/compare
  and supersession invalidation.
- [ ] Keep export text permanently explicit: artifact produced, not posted/executed/closed in BRAVO.

Exit: one coherent shell renders Chat and all three AccountingCase workspaces, with no duplicate
frontend state machine and no legacy Financial Close mock in the normal demo path.

### DEMO18-06 — demo identities, permissions and deterministic reset

- [ ] Update the idempotent demo seed contract so the accounting maker has the required own-dept
  read/create capabilities and the chief-accountant reviewer has own-dept read/review capabilities.
- [ ] Retain `doc:read:own_dept` for both identities so Knowledge Chat can be demonstrated without an
  admin bypass.
- [ ] Prove maker cannot review/export its own submitted payload and reviewer can act only within
  authorized department scope.
- [ ] Keep an outside-department identity for non-disclosure probes.
- [ ] Add a deterministic reset/seed command that does not delete unrelated user/customer data and
  is explicitly restricted to the synthetic demo environment.
- [ ] Document demo accounts without embedding secrets in frontend code, screenshots, URL query or
  committed runtime logs.

Exit: `/api/me` returns the intended capabilities for maker/reviewer/outside-department identities;
positive and negative HTTP tests prove server authority. No demo relies on the admin identity.

### DEMO18-07 — security, hard states, accessibility and responsive completion

- [ ] Cover `401`, `403`, scoped `404`, `409`, `422`, `429`, `5xx`, network loss, stream error,
  offline and session expiry for both modules.
- [ ] Ensure denied labels, counts, source titles, case IDs, evidence lineage and prefetches are absent
  from the DOM/network trace.
- [ ] Test token clearing and safe return paths without sharing state with `frontend-react`.
- [ ] Prevent duplicate send/create/review/export actions and preserve idempotency keys across safe
  transport retry.
- [ ] Run axe/WCAG 2.2 AA checks on sign-in, Chat home/history/workspace/shared and all three case
  workspaces.
- [ ] Verify keyboard-only composer, evidence rail, dialogs/drawers, maker review and export.
- [ ] Verify 200% zoom, 44px mobile targets, 390/768/1024/1440 layouts, light/dark/system themes and
  reduced motion.
- [ ] Review all Vietnamese copy for exact-claim, draft-only and evidence-gap language.

Exit: zero P0/P1 scope leak, unsafe mutation, approval bypass, false evidence claim or critical axe
finding; remaining lower-severity findings have owner-approved dispositions.

### DEMO18-08 — live local API and browser verification

- [ ] Rebuild/start Postgres, Redis and API with the deterministic host-port override and confirm
  health/auth configuration.
- [ ] Apply/verify migration `0020_case_v2_audit` and seed the demo identities in the containerized
  runtime.
- [ ] Run a real Knowledge Chat POST-SSE lifecycle. If the configured model/runtime is unavailable,
  record it as a blocker; do not substitute a fixture response for the live exit.
- [ ] Run two isolated browser contexts: maker and reviewer.
- [ ] For Bank, Voucher and Period: maker create → evidence → checks → handoff; reviewer reload →
  review → export; then verify maker-checker and stale revision negative cases.
- [ ] Verify conversation ownership/non-owner `404`, source/attachment ownership and shared-token
  read-only behavior.
- [ ] Run candidate typecheck, all Vitest suites, live Playwright suites and production build.
- [ ] Run the classic comparator's existing gates without editing it.

Exit: machine-readable logs and screenshots prove the live paths; there is no request interception
or mocked success in the live suite.

### DEMO18-09 — packaging, rehearsal and internal-demo evidence

- [ ] Provide one documented local launcher for database/API/seed/frontend with preflight checks and
  actionable port/dependency errors.
- [ ] Provide stop/restart/reset instructions and a quick health checklist.
- [ ] Produce candidate and classic bundle hashes plus rollback/select instructions; production
  cutover remains disabled.
- [ ] Capture the final responsive visual matrix after data and copy are stable.
- [ ] Run a timed owner rehearsal using the script in section 8 and record deviations.
- [ ] Publish a final evidence packet containing scope, limitations, gate logs, account/role matrix,
  route/API matrix, screenshots, known issues and deferred external gates.
- [ ] Ensure the UI and packet say `synthetic`, `internal demo`, and `artifact not executed` wherever
  required.

Exit claim allowed: `FigmaMake V2 local synthetic internal demo ready for owner evaluation`.

### DEMO18-10 — closure record

- [x] Mark Plan 17 FEV2-10 complete only if all three live two-identity lifecycles and bundle/
  rollback evidence passed.
- [x] Mark Plan 18 complete only if Knowledge Chat and Accounting Operations both passed their live
  exits and there are no dead/mocked normal routes.
- [ ] Update `docs/PROJECT-STATE.md`, `docs/AI-REVIEW-MANIFEST.md` and evidence indexes with exact
  evidence paths and remaining external gates.
- [ ] Record owner acceptance or rejection separately from automated developer evidence.

No completion record may claim conversation-quality superiority, SME correctness, customer-data
permission, pilot eligibility or production readiness.

## 8. Internal demo script

Target duration: 12–15 minutes after preflight.

1. Sign in as the accounting maker; show returned identity/scope without exposing tokens.
2. Open Knowledge Chat, ask a BRAVO/accounting question, observe live streaming, select a returned
   citation and show the contextual evidence/no-evidence truth state.
3. Reload the conversation to prove durable history; optionally show a safe attachment/source turn
   and read-only share.
4. Open `Công việc AI`; create Bank Reconciliation, attach frozen server evidence and run checks.
5. Inspect one finding's evidence, rule and hash lineage; hand off for review.
6. Sign in in a separate browser context as the chief-accountant reviewer; review and export the
   non-executing artifact.
7. Repeat the bounded happy path for Voucher and Period Close; emphasize reuse of the shared core
   and the absence of posting/close controls.
8. Show one deliberate negative case: maker self-review denial or stale-revision `409`.
9. End on limitations: synthetic data, local runtime, no ERP mutation, external/SME/production gates
   still open.

## 9. Verification matrix

| Gate | Minimum proof |
|---|---|
| Contract | strict auth/conversation/SSE/AccountingCase decoders and frozen examples |
| Functional | live Chat lifecycle plus three live two-identity case lifecycles |
| Authorization | maker/reviewer/outside-dept/admin-free positive and negative probes |
| Evidence | citations or truthful absence; case snapshot/rule/hash lineage |
| Concurrency | chat busy/abort and AccountingCase revision/idempotency conflict |
| Accessibility | axe, keyboard, focus lifecycle, live regions, 200% zoom, 44px mobile targets |
| Responsive | 1440×900, 1024×768, 768×1024 and 390×844 in light/dark |
| Build | frozen-lockfile install, typecheck, tests, production build and deep-link serving |
| Packaging | launcher/preflight, candidate/classic hashes and rollback procedure |

Expected candidate commands after scripts are normalized:

```powershell
Set-Location FigmaMake_UI
corepack pnpm run typecheck
corepack pnpm run test
corepack pnpm run test:auth
corepack pnpm run test:contract
corepack pnpm run test:a11y
corepack pnpm run test:visual
corepack pnpm run test:e2e
corepack pnpm run build
```

Because Corepack installation can fail with `EPERM` under `C:\Program Files\nodejs`, the launcher
must also support checked-in `node_modules` binaries where present and produce a clear dependency
instruction rather than hang.

## 10. Risk register

| Risk | Impact | Control |
|---|---|---|
| Live chat provider/model unavailable | Chat appears pending or fails during demo | preflight an actual SSE turn; block live exit rather than use hidden mock |
| Seed identities lack V2 permissions | Accounting Work hidden/403 | version and test idempotent maker/reviewer seed |
| Fixture/live provider crossover | false completion or data disclosure | provider boundary, fixture-ID rejection, QA zero-network tests |
| SSE parser mishandles chunking/abort | hanging or duplicate response | frozen parser vectors plus live browser test |
| Evidence citations lack metadata | UI invents scope/status | render only returned fields and explicit unavailable state |
| Dirty worktree obscures scope | unrelated changes lost or misattributed | baseline/diff inventory; no cleanup/reset; scoped review |
| Three-column shell collapses poorly | evidence or actions inaccessible | drawer/focus/zoom/mobile matrix before visual sign-off |
| Legacy routes remain discoverable | demo looks incomplete or misleading | normal-nav containment and route/network DOM probe |
| “Complete V2” overstated | governance/release error | separate demo exit from SME, A/B/C/D, real-data and production gates |

## 11. Stop conditions

Stop and request owner/council direction if:

- completing a screen requires the browser to calculate or assert accounting truth;
- the live Chat route requires broad patching of the legacy agent loop, prompt, retrieval, routing,
  critic or synthesis rather than adapting the FE to its frozen contract;
- a required evidence/source field is absent and cannot be shown truthfully as unavailable;
- an implementation would weaken RLS, maker-checker, approval, revision/idempotency, offline or
  controlled-egress controls;
- live and QA fixture providers cannot be separated;
- local Chat cannot produce one actual terminal SSE turn with the approved runtime;
- an unapproved route expands the demo into legacy tool parity, real ERP mutation, production
  cutover or customer data.

## 12. Definition of done

Plan 18 is complete only when all of the following are true:

1. Normal FigmaMake navigation contains only live, authorized V2 demo modules/surfaces.
2. Knowledge Chat uses real auth, conversation CRUD and POST-SSE contracts; durable reload works.
3. Chat evidence is citation-backed or explicitly absent; no illustrative evidence remains live.
4. Accounting Work completes Bank, Voucher and Period through a maker plus different reviewer.
5. No frontend business calculation, autonomous mutation, self-approval or hidden fixture success
   exists in the normal demo path.
6. Auth/RLS, capability, revision/idempotency, evidence/hash and non-execution invariants fail closed.
7. Loading, empty, denied, conflict, network/offline, stream-error and session-expiry paths are usable.
8. Typecheck, unit/contract, live browser, accessibility, responsive visual and build gates pass.
9. One launcher, reset guide, demo script, bundle hashes and rollback instructions are preserved.
10. The final evidence packet records the exact bounded claim and every deferred external gate.

Completion of these ten items permits an internal-demo claim only. Program-level V2 completion
still requires the separately governed conversation-quality, blind SME and external release gates.

## 13. First execution handoff

```text
Objective:
Execute DEMO18-00, then DEMO18-01. Do not begin live Chat rendering before the route/provider
boundary and contract snapshot are frozen.

First actions:
1. Record baseline/diff/runtime migration and re-run current candidate gates.
2. Reconcile Plan 17 status text with its actual implementation evidence.
3. Freeze the route/data-source matrix and Knowledge Chat endpoint/SSE examples.
4. Refactor normal App routes away from AppContext fixtures while preserving explicit QA routes.
5. Reduce live navigation to Knowledge Chat, Công việc AI and authorized live sources.

Do not:
- clean/reset the dirty worktree;
- edit frontend-react;
- expose legacy tool menus in the normal demo;
- add a mocked live Chat success;
- change prompts/retrieval/model behavior;
- claim Plan 17/18 complete before live two-identity and live SSE evidence exists.

Verification at the first stop:
- git diff --check;
- current FigmaMake typecheck/test/build;
- fixture-ID and normal-route isolation tests;
- updated route/source matrix and Plan 17 status evidence.
```
