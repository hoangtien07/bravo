# BRAVO V2 FE-only owner review pack

Status: `READY_FOR_OWNER_REVIEW — INTEGRATION LOCKED`

This package is a fixture-only review surface. It does not authenticate a real user, call an API,
open SSE, upload a file, approve/export a real draft, or execute any ERP operation.

## Direct review entry points

- `/review?qa=1&scenario=ROUTE-01&theme=light` — searchable index for all 171 tracker case IDs.
- `/login?qa=1&scenario=AUTH-04&theme=light` — simulated authentication failure.
- `/c/fixture:review?qa=1&scenario=CHAT-20&theme=light` — conversation capabilities.
- `/financial-close?qa=1&scenario=CLOSE-04&state=conflict&theme=dark` — governed close conflict.
- `/approvals?qa=1&scenario=DRAFT-08&theme=light` — maker-checker review.
- `/tools/money-engine?qa=1&scenario=MONEY-06&theme=dark` — operational parity page.
- `/shared/fixture:review?qa=1&scenario=SHARE-01&theme=light` — public read-only projection.

Each case URL accepts `role`, `capability`, `scenario`, `state`, and `theme`. The in-app index is
generated from `src/fixtures/caseRegistry.ts`, whose automated test freezes 171 unique IDs.

## Representative screenshots

- `1440-review-light.png` — complete review index, desktop light.
- `1024-close-dark.png` — Financial Close conflict, compact desktop dark.
- `768-approvals-light.png` — approval queue/detail, tablet light.
- `390-money-dark.png` — Money Engine, mobile dark.

The screenshots are deterministic illustration views. They are not production or integration
evidence.

## Role and capability comparison

| Fixture | Navigation/affordance expectation |
|---|---|
| Accountant | No approval or administration affordance. |
| Chief accountant | Approval and governed Financial Close review; no administration. |
| Finance manager | Approval and evidence review; no administration. |
| Consultant | Conversation/Knowledge/graph support; no approval. |
| Administrator | Administration plus configured review affordances. |
| Offline local | Local-approved evidence only; missing cloud evidence remains unconfirmed. |
| Limited/cloud blocked | Affected controls explain the boundary; no silent cloud fallback. |

These are presentation fixtures only. Backend authorization and RLS remain authoritative later.

## Business invariants reviewed

- Conversation: outcome, prerequisites, evidence, next action and uncertainty remain visible;
  stop/edit/regenerate/share/feedback/attachment actions are local simulation only.
- Financial Close: exactly eight governed groups, no unexplained readiness percentage, and every
  ready/conflict/missing conclusion stays evidence-dependent.
- Drafts: proposed, validated, approved, exported, executed and verified remain distinct; expected
  revision, missing checks and maker-checker block unsafe transitions.
- Knowledge: scope and supplied governance metadata remain visible; unavailable fields are not
  invented and inaccessible file content is never previewed.

## Verification

```text
pnpm run typecheck   PASS
pnpm run test        PASS — 3 files / 7 tests
pnpm run test:a11y   PASS — no critical axe violations in review-index smoke
pnpm run test:visual PASS — four viewport × light/dark manifest
pnpm run build       PASS — operational tool route emitted as a lazy chunk
```

## Deliberate omissions / unsupported live data

- No live company, branch, accounting period, BRAVO version, financial amount, schema or execution
  result is supplied.
- Financial Close readiness and its dependency graph remain synthetic projections.
- No backend contract, prompt, retrieval, migration, Docker, CI or classic frontend was changed.
- Automated pixel-diff baselines are not introduced; the four checked screenshots are the visual
  owner-review samples for this FE-only gate.
- Conversation-quality A/B/C/D evidence is outside this UI verdict.

## Gate

Do not start INT-00 or FM-01. The project owner must record `APPROVED`, `CHANGES_REQUESTED`, or
`REJECTED` in the tracker after reviewing this package.
