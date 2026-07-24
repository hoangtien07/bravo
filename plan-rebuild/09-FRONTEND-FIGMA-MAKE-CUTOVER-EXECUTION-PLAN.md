# BRAVO V2 frontend — Figma Make productization and cutover plan

Status: `READY FOR IMPLEMENTATION — local Figma Make productization authorized`
Owner: project owner
Decision updated: 2026-07-21
Repository baseline: `feat/v2-p0-containment` at `f17d31c079f8de71f0ffc303495f3176eef59d23`
Candidate V2 frontend: `FigmaMake_UI/`
Classic baseline/rollback frontend: `frontend-react/`

---

## 1. Owner direction and purpose

Develop the approved Figma Make experience directly in `FigmaMake_UI` as the candidate BRAVO V2
frontend. It must run locally as its own application first, then replace simulated runtime behavior
with the existing real FastAPI auth, API and SSE contracts. If it reaches parity and the release
gates pass, its immutable bundle becomes the candidate for the one-time production cutover.

`frontend-react` is no longer the implementation target for the new visual experience. Keep it
unchanged as the functional comparator and rollback source during this program. Do not import V2
components into it, upgrade its dependencies, or remove it before the rollback window closes.

This decision supersedes the earlier rule that `FigmaMake_UI` was design-reference-only. It does
not weaken backend authorization, RLS, evidence, financial-integrity, maker-checker, offline or
release-containment requirements.

## 2. Start here in a new chat

Read in this order before editing:

1. `docs/PROJECT-STATE.md`
2. `docs/AI-REVIEW-MANIFEST.md`
3. `plan-rebuild/08-V2-CONVERSATION-REBUILD-HANDOFF.md`
4. `plan-rebuild/04-WORKSPACE-REPO-COUNCIL-DECISION.md`
5. `plan-rebuild/07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`
6. this plan
7. `FigmaMake_UI/AGENTS.md`
8. `FigmaMake_UI/src/imports/DESIGN.md`
9. `FigmaMake_UI/PRODUCT-LOGIC.md`
10. `FigmaMake_UI/DESIGN-QA-RESULTS.md`
11. `FigmaMake_UI/plans/10-LOCAL-CONTINUATION-CHECKPOINT.md`
12. current `frontend-react` API/store behavior only when verifying a named contract

Code, tests, migrations and runtime evidence override prose. Do not read `.env` values or copy
secrets. Do not edit reference repositories outside this workspace.

## 3. Verified starting state

### Repository

- Branch/commit: `feat/v2-p0-containment` / `f17d31c079f8de71f0ffc303495f3176eef59d23`.
- Alembic head verified through `.venv`: `0017_native_rls_backstop`.
- User-owned untracked content includes `FigmaMake_UI`, the Figma audit and this plan.
- The accidental 2026-07-21 React 19/Vite 8/V2-shell changes in `frontend-react`, Docker and CI
  were fully reverted before this plan was written.

### Classic frontend

- Location: `frontend-react/`.
- React 18, Vite 5, Tailwind 3.
- Baseline verification: typecheck PASS; 3 files/7 tests PASS; production build PASS.
- It already owns real password/OIDC auth, `/api/me`, React Router, API client, POST+SSE chat,
  stop/cancel, attachments, invoice upload, conversation CRUD/share/truncate, feedback, citations,
  drafts, Knowledge, Admin, Money Engine, Anomaly, Tax and generic Graph behavior.
- Treat this behavior as a compatibility reference, not as code to copy wholesale.

### Candidate V2 frontend

- Location: `FigmaMake_UI/`.
- React 19.2.4, Vite 8.0.3, Tailwind 4.2.2, TypeScript 5.9.3, pnpm lockfile.
- TypeScript and production build passed at the recorded baseline.
- It contains the approved visual system and responsive screen compositions.
- It currently contains fake auth, screen-switch state, timers, local approval simulation and
  synthetic Financial Close data. None of those is a production security or data boundary.

## 4. Product target

Subject: BRAVO evidence-led operational workspace for accountants, chief accountants, finance
managers, BRAVO consultants and authorized administrators.

Single primary job: help a user reach the next safe, evidence-backed action in a BRAVO task without
mistaking a draft, fixture, inference or unverified claim for an executed ERP result.

Visual direction: **Assured Operations — Quản trị chắc chắn, có bằng chứng**.

- Use official BRAVO green and the accessible teal extension.
- Use the official logo asset without recoloring or distortion.
- Keep typography disciplined and operational, with tabular numerals.
- Use the paired `//` motif only for evidence/progress/relationship meaning.
- Avoid generic AI gradients, glassmorphism, decorative dashboards and unexplained scores.
- Support full light/dark themes, 1440/1024/768/390 widths, keyboard use, reduced motion and 200%
  zoom.

## 5. Locked boundaries

### Must remain outside the frontend

- Authorization and RLS enforcement.
- Conversation ownership.
- Exact financial calculations and evidence validation.
- Maker-checker and draft transition authorization.
- Prompt, retrieval, routing, critic, model and synthesis behavior.
- ERP execution; generated SQL/config/accounting output is never executed automatically.

### Program scope

- Productize `FigmaMake_UI` into a real React SPA.
- Preserve its approved design language while replacing simulation infrastructure.
- Integrate existing backend contracts without adding endpoints merely to satisfy a mock screen.
- Use explicit synthetic fixtures only for unbacked Financial Close presentation surfaces.
- Keep `frontend-react` runnable and untouched for comparison/rollback.

### Non-goals

- No backend or migration changes in this frontend program without a separately approved gap.
- No conversation-quality claim from UI work.
- No second production frontend exposed to normal users.
- No copying `AppContext`, `QAContext`, timer streaming or local approval functions into the real
  runtime path.

## 6. Target local and production architecture

```text
Local development

FigmaMake_UI (Vite, candidate V2 port)
    |  /api, /shared proxy
    v
Existing FastAPI backend
    |-- JWT/OIDC and /api/me
    |-- conversation ownership and POST+SSE
    |-- documents/source RLS
    |-- drafts and maker-checker
    `-- admin/tool APIs

Classic comparator

frontend-react (unchanged, separate dev port/build)
    `-- same backend contracts

Production after acceptance

FastAPI /static/ -> one immutable accepted FigmaMake_UI bundle
Rollback          -> retained immutable frontend-react bundle
```

During local development both frontends may run on different ports against the same authorized
development backend. Do not mix their bundles, localStorage namespaces or routing state.

## 7. Candidate application structure

Refactor toward this ownership model; exact filenames may adapt to current source:

```text
FigmaMake_UI/src/
  app/              router, providers, protected layout, error boundaries
  api/              client, auth headers, normalized errors, SSE parser, DTOs
  auth/             password/OIDC/session expiry/protected redirect
  capabilities/     frontend affordance and prefetch decisions
  design/           tokens, primitives, logo rules, themes, responsive shell
  conversation/     real store, history, SSE, stop, upload, evidence, drafts
  features/         knowledge, approvals, admin and operational tools
  financial-close/  explicitly synthetic readiness/graph projections
  fixtures/         scenario data and zero-network simulation reducer
  test/             API mocks, fixtures and deterministic clocks
```

UI components consume typed services/stores. They do not call `fetch` ad hoc and do not infer
permissions from hidden controls.

## 8. Runtime contracts

### 8.1 Data origin

```ts
type SurfaceData<T> =
  | { origin: "live"; data: T }
  | {
      origin: "synthetic_fixture";
      data: T;
      scenarioId: string;
      illustration: true;
    };
```

- Live and synthetic arrays are never concatenated.
- Fixture IDs use `fixture:` and are rejected before any request is built.
- Fixture screens render a global illustration banner plus local origin labels.
- Fixture actions begin with `Mô phỏng`, update local revision-aware state and make zero mutation
  requests.
- Production fixture access requires `Identity.is_admin` plus explicit per-session illustration
  activation. Logout/session end clears activation.

### 8.2 Capability mirror

```ts
type ScopeLevel = "all" | "own_dept" | null;
scopeLevel(identity, resource, action): ScopeLevel;
```

- Admin resolves to `all`.
- `{resource}:{action}:all` resolves to `all`.
- `{resource}:{action}:own_dept` resolves to `own_dept`.
- Missing scoped permission resolves to `null`.
- Frontend checks control affordances and prefetch only; backend remains authoritative.

Action mapping:

- Knowledge read/file: `doc:read:*`.
- Source upload/visibility: existing source-write contract.
- Approval list/approve/reject/export: `draft:approve:*`.
- Money/Anomaly/Tax creation actions: `draft:create:*`.
- Admin: `is_admin` plus server checks.

### 8.3 Conversation compatibility

Preserve the current contract exactly until backend evidence says otherwise:

- Client owns the conversation identifier used by the current flow.
- Message submission uses the existing POST+SSE endpoint and event grammar.
- Preserve abort/stop and ignore late events after cancellation.
- Preserve attachments, invoice upload, citations, artifacts, draft events, steps, grounded/cloud
  metadata, edit/regenerate/truncate, feedback/report and share behavior.
- Do not change prompts or request semantics while changing presentation.

### 8.4 Async screen states

Every real data route owns loading, ready, empty, recoverable error, 403 permission, session expiry
and offline/limited capability states. Add stale/conflict states where the API supplies revision or
evidence status. A 403 is not an empty list.

## 9. Route target

| Route | Source | Rule |
|---|---|---|
| `/login` | auth config/login/OIDC | public, preserve validated `next` |
| `/` | real conversations/chat | authenticated new conversation |
| `/c/:id` | real conversation/SSE | owner/admin via backend |
| `/conversations` | real API | authenticated |
| `/knowledge` | real sources API | `doc:read:*` |
| `/approvals` | real drafts API | `draft:approve:*` |
| `/admin` | real admin APIs | admin only |
| `/tools/money-engine` | real invoice/draft APIs | per action capability |
| `/tools/anomaly` | real anomaly/draft APIs | per action capability |
| `/tools/tax` | real tax/draft APIs | per action capability |
| `/tools/knowledge-graph` | real `/api/graph` | `doc:read:*` |
| `/financial-close` | synthetic fixture | illustration eligibility/session |
| `/financial-close/graph` | synthetic fixture | illustration eligibility/session |
| `/shared/:token` | real shared API | read-only token surface |

Legacy route aliases may redirect inside the candidate SPA. The Financial Close graph is not the
generic `/api/graph` response.

## 10. Work packages and dependency order

| WP | Work package | Status |
|---|---|---|
| FM-00 | Freeze baseline and protect classic frontend | COMPLETE |
| FM-01 | Candidate runtime foundation and test harness | NOT_STARTED |
| FM-02 | Real auth, router and protected responsive shell | NOT_STARTED |
| FM-03 | Real Conversation V2 surface over existing SSE | NOT_STARTED |
| FM-04 | Knowledge, Approvals and Admin integration | NOT_STARTED |
| FM-05 | Money, Anomaly, Tax and generic Graph parity | NOT_STARTED |
| FM-06 | Synthetic Financial Close isolation | NOT_STARTED |
| FM-07 | Integrated accessibility/security/visual verification | NOT_STARTED |
| FM-08 | Immutable build, staging cutover and rollback | NOT_STARTED |

Only one package is `IN_PROGRESS`. Update this table, its checklist and the handoff whenever work
stops.

### FM-00 — completed baseline

- [x] Confirm `frontend-react` is restored to Git baseline.
- [x] Preserve `FigmaMake_UI` as user-owned candidate source.
- [x] Record commit and Alembic head.
- [x] Verify both frontend baselines at least once.
- [x] Record that WP-00A remains a release gate, not a local FE development gate by owner decision.

### FM-01 — runtime foundation

- [ ] Keep React 19/Vite 8/Tailwind 4/pnpm; validate the lockfile and Node engine.
- [ ] Remove Figma-host-specific assumptions from the local build without losing Figma portability
  unless owner chooses local-product runtime as authoritative.
- [ ] Add environment-safe API base/proxy configuration; never embed credentials.
- [ ] Add React Router, API client, SSE parser, typed DTO boundary and normalized errors.
- [ ] Add Vitest/Testing Library plus Playwright/axe/visual scripts.
- [ ] Separate `fixtures` from live services and add fixture-ID rejection tests.
- [ ] Add deterministic clocks, locale, timezone, reduced motion and viewport matrix.

Exit: clean install, typecheck, unit smoke and production build pass; no real request is made by a
fixture mutation.

### FM-02 — auth and shell

- [ ] Replace fake auth with password/OIDC config, callback, `/api/me`, logout and expiry handling.
- [ ] Implement protected deep-link redirect and safe return.
- [ ] Replace screen-switch reducer with routes from section 9.
- [ ] Implement expanded/compact/mobile shell, focus lifecycle and capability-filtered navigation.
- [ ] Preserve unknown company/branch/period/version as unknown.
- [ ] Complete Light/Dark/System with flash-free initialization.

Exit: login and protected-route tests pass at 1440/1024/390; non-admin cannot discover or prefetch
Admin data.

### FM-03 — conversation

- [ ] Replace simulated timers with the existing POST+SSE protocol.
- [ ] Implement new conversation, stable URL transition and recent history.
- [ ] Implement streaming, status, stop, late-event suppression and recovery.
- [ ] Implement attachments/invoice upload, citations/evidence, draft cards and share.
- [ ] Implement edit/regenerate/truncate, feedback/report and Consultant profile/state.
- [ ] Preserve desktop evidence aside and mobile evidence sheet focus behavior.

Exit: contract tests cover exact request/event grammar; no prompt/retrieval/backend change; classic
and candidate can execute the same frozen interaction against the same backend.

### FM-04 — governed data surfaces

- [ ] Knowledge list/upload/delete/file access with scoped capabilities and all async states.
- [ ] Approval list/approve/reject/export with maker-checker negative case.
- [ ] Admin users/departments/permissions/usage/feedback with admin-only fetch boundaries.
- [ ] Render only fields actually supplied by current APIs; unavailable governance metadata is
  explicitly unavailable.

### FM-05 — operational parity

- [ ] Money Engine authorized upload/draft/review/export subsets.
- [ ] Anomaly authorized scan/review subsets.
- [ ] Tax authorized reconcile/review subsets.
- [ ] Generic knowledge graph with source opening and Ask AI handoff.
- [ ] Lazy-load all tool/graph modules outside the initial conversation route.

### FM-06 — Financial Close illustration

- [ ] Implement eight governed prerequisite groups and required status explanations.
- [ ] Implement graph/list/table, search/filter/fit/reset and accessible inspector.
- [ ] Mobile defaults to list view.
- [ ] Enforce `SurfaceData`, `fixture:` IDs, explicit activation and zero-network mutations.
- [ ] Never modify real Approval counts or claim ERP readiness/execution.

### FM-07 — integrated verification

- [ ] Typecheck, unit/contract tests and production build from clean install.
- [ ] E2E: login/deep link, conversation/SSE/stop/upload/share, approvals and route aliases.
- [ ] Security probes: two users, two departments, non-approver, non-admin, fixture-ID rejection.
- [ ] Axe and keyboard checks on every route/state; focus trap/restore; 200% zoom; 44px targets.
- [ ] Visual matrix: 1440x900, 1024x768, 768x1024 and 390x844 in light/dark.
- [ ] Initial conversation bundle excludes Admin, graph, Mermaid and unused KaTeX.

### FM-08 — cutover

- [ ] Produce immutable candidate and classic artifacts.
- [ ] Decide how Docker/FastAPI selects the candidate bundle in one reviewed infrastructure change.
- [ ] Stage with real auth/API/SSE/deep-link serving.
- [ ] Obtain owner visual and functional sign-off.
- [ ] Run post-deploy smoke and monitor auth/SSE/frontend/API error changes.
- [ ] Record rollback owner, duration and closure criteria.
- [ ] Remove classic source only in a later, separately approved cleanup.

## 11. Verification commands

Use repository reality if scripts evolve; update this section when commands change.

Candidate baseline/current commands:

```powershell
Set-Location FigmaMake_UI
pnpm.cmd install --frozen-lockfile
.\node_modules\.bin\tsc.cmd --noEmit
pnpm.cmd run build
```

FM-01 must add non-interactive scripts equivalent to:

```powershell
pnpm.cmd run typecheck
pnpm.cmd run test
pnpm.cmd run test:e2e
pnpm.cmd run test:a11y
pnpm.cmd run test:visual
pnpm.cmd run build
pnpm.cmd list
```

Classic regression comparator:

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
git diff --stat
git diff -- FigmaMake_UI
git diff -- frontend-react
```

## 12. Containment and release boundary

The owner authorized local candidate FE development before the old WP-00/WP-00A evidence gates
complete. Those gates still block staging/production/cutover claims:

- provider credential rotation confirmation;
- production network and credential hardening;
- legacy agent owner authorization runtime probe;
- API/worker egress alignment;
- backup plus isolated restore drill;
- final-answer guard parity;
- state CAS/idempotency/corrupt recovery;
- atomic audited review transitions;
- native RLS probes through separate HTTP/MCP/worker roles;
- frozen A/B manifest with resolvable checksums.

Do not present local FE success as proof that these controls passed.

## 13. Stop conditions

Stop and request owner direction when:

- integration requires changing a backend contract rather than adapting the candidate frontend;
- a synthetic and live projection cannot be reliably separated;
- auth/RLS/maker-checker behavior would be weakened;
- exact current SSE behavior cannot be preserved;
- candidate dependency choices break the offline production build;
- a screen requires data the backend does not expose and cannot truthfully display as unavailable;
- work would modify prompts, retrieval, routing, critic or synthesis.

## 14. Definition of done

The Figma Make cutover is complete only when:

1. `FigmaMake_UI` is a real routed application using existing auth/API/SSE contracts;
2. current classic capabilities have verified parity or an owner-approved omission;
3. real and synthetic data cannot be mixed or confused;
4. authorization, evidence, maker-checker and offline invariants remain intact;
5. responsive, theme, accessibility, contract, E2E and visual gates pass;
6. the candidate bundle works through the real FastAPI static/deep-link path;
7. containment/release evidence and owner sign-off pass;
8. the immutable classic artifact and rollback procedure remain available;
9. UI success is reported separately from conversation-quality A/B/C/D evidence.

## 15. Handoff for the next chat

```text
Objective:
Productize FigmaMake_UI as the BRAVO V2 candidate frontend. Do not implement the new UI in
frontend-react and do not change the backend.

Current status:
- FM-00 COMPLETE.
- FM-01 is the next package and is NOT_STARTED.
- frontend-react is restored and must remain the classic comparator/rollback source.
- FigmaMake_UI typecheck/build passed at the recorded baseline, but it still uses fake auth,
  screen-switch state, simulated streaming and local approval behavior.
- WP-00A/containment remains a production release gate, not a local FE development gate.

First exact implementation action:
1. Re-read sections 6-10 of this plan.
2. Inspect FigmaMake_UI package/config/App/AppContext/QAContext and frontend-react API/SSE/auth
   contracts without editing frontend-react.
3. Mark FM-01 IN_PROGRESS.
4. Add the candidate runtime boundary: React Router, API client, SSE parser, typed live-vs-fixture
   services and tests.
5. Keep every existing Figma screen rendering while replacing infrastructure incrementally.

Do not:
- copy the classic UI into FigmaMake_UI;
- import Figma fake auth/timers/approval reducer into live services;
- send fixture IDs to APIs;
- invent missing company/period/version/evidence fields;
- edit prompts, retrieval, backend routes or migrations.

Verification before handoff:
- candidate typecheck/test/build;
- git diff --check;
- confirm git diff -- frontend-react is empty;
- update dashboard, checklist, evidence and this handoff.
```
