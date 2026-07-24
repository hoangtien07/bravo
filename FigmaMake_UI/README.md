# Bravo Agent AI — Figma Make UI

Interactive React prototype for the Bravo Agent AI Conversation Core V2 experience and its first deep vertical slice: **Financial Close Advisor**.

This folder is an executable UX specification and design reference. It is **not** the production BRAVO frontend and does not provide real authentication, API integration, RLS enforcement, persistence, approval, or ERP execution.

## What is included

- Sign-in and trusted-shell visual composition.
- New and active advisory conversation screens.
- Financial Close readiness rail with eight governed prerequisite groups.
- Financial Close evidence graph with graph, accessible list, and table views.
- Evidence details and governed knowledge-library views.
- Draft review with revision-aware, fail-closed lifecycle transitions.
- Role-gated Administration prototype.
- Responsive layouts for desktop, compact desktop, and 390px mobile.
- Design QA mode with typed roles, capabilities, scenarios, and component states.

All runtime records are synthetic fixtures. Illustration data is explicitly labelled and must never be treated as real company, financial, schema, version, approval, execution, or verification evidence.

## Requirements

- Node.js compatible with the lockfile and Vite 8.
- pnpm through Corepack or a local pnpm installation.

## Install and run

```powershell
pnpm install
pnpm run dev
```

The default Figma Make development port is `8443`. To use another local port:

```powershell
pnpm run dev -- --host 127.0.0.1 --port 4174
```

Build the production bundle:

```powershell
pnpm run build
```

Run the strict TypeScript check on Windows:

```powershell
.\node_modules\.bin\tsc.cmd --noEmit
```

## Design QA mode

Add `?qa=1` to the preview URL:

```text
http://127.0.0.1:8443/?qa=1
```

The QA panel can switch:

- role and fixture-level navigation permissions;
- online, offline-local, limited, and cloud-blocked capability states;
- unknown, partial, conflicting, ready, permission-limited, and offline scenarios;
- default, loading, empty, error, permission-denied, stale, conflict, success, and offline UI states.

QA permissions are presentation fixtures only. They do not replace server-side authorization or database RLS.

## Important files

| Path | Purpose |
|---|---|
| `src/App.tsx` | Screen composition and shared QA-state boundary |
| `src/context/AppContext.tsx` | Deterministic local application reducer |
| `src/context/QAContext.tsx` | QA-mode settings and scenario loading |
| `src/state/types.ts` | Canonical task, evidence, prerequisite, draft, and QA types |
| `src/fixtures/scenarios.ts` | Clearly labelled synthetic fixtures |
| `src/components/` | Product screens and shared UI primitives |
| `src/imports/DESIGN.md` | Approved product-design specification |
| `PRODUCT-LOGIC.md` | Deterministic UX and lifecycle rules |
| `DESIGN-QA-RESULTS.md` | Verification record and residual limitations |
| `plans/10-LOCAL-CONTINUATION-CHECKPOINT.md` | Current checkpoint and production-conversion plan |

## Product invariants

- Unknown scope remains unknown; the default view does not invent company, period, environment, or BRAVO version.
- Exact financial, schema, version, execution, approval, and verification claims require matching evidence.
- Draft, approved, exported, externally executed, and verified are distinct lifecycle states.
- The prototype never executes SQL, configuration, accounting entries, or other ERP mutations.
- Profile selection does not widen permissions or evidence visibility.
- The Financial Close graph represents governed prerequisites and evidence, not a generic knowledge graph.

## Production handoff

Do not replace `frontend-react` with this exported application. Port the visual tokens and selected component compositions into the existing trusted frontend behind a feature flag, while retaining its real router, auth store, API client, SSE, attachments, abort handling, and permission enforcement.

The next implementation sequence is documented in `plans/10-LOCAL-CONTINUATION-CHECKPOINT.md`.
