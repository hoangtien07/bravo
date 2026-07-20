# Google Stitch setup - Bravo Agent AI

This checklist is the operational companion to the root `DESIGN.md`.

## Form fields

### Paste existing DESIGN.md

Paste the complete contents of `DESIGN.md` from the repository root.

### Upload code, images, fonts, and icons

Upload only:

1. `docs/design/assets/bravo-logo.png`
2. `docs/design/assets/bravo-logo-slogan-vi.png`

Do not upload the legacy ISO logo lockup, company-name lockups, `.ai` source files, or current
frontend CSS as visual references. The current frontend palette is not the approved target palette.

### Upload a .fig file

Leave empty for the first exploration. Add a `.fig` file only after one direction is approved.

### Public GitHub repository

Leave empty. Do not make the private bravo-v2 repository public for Stitch ingestion.

### Add website

Leave empty in round one. The Brand Guidelines and official logos are the governing sources.

### Additional instructions

```text
Design a Vietnamese, desktop-first internal ERP application named Bravo Agent AI.
This is not a landing page. Start with Financial Close Advisor and use realistic business labels
without inventing financial amounts, database objects, menu paths, or verified completion claims.

Keep the official BRAVO logo unchanged. Display "Agent AI" as editable product text beside the
official logo. BRAVO green is dominant and orange is only an attention accent.

Use the paired 29-degree // motif as a meaningful evidence/progress/graph marker, not repetitive
decoration. Prioritize clarity, traceable evidence, authorization, and draft/approval boundaries.

Create complete empty, loading, error, missing-evidence, conflict, permission-denied, offline, and
responsive states. Do not use purple AI gradients, glassmorphism, robots, brains, sparkles, glowing
graph nodes, animated particles, fake dashboards, or invented KPI values.
```

## Generation order

Do not generate the entire application in one prompt. Work in this order:

1. Design Foundation and component states.
2. Sign in and Application Shell.
3. New Conversation.
4. Active Conversation and Evidence Drawer.
5. Financial Close Readiness.
6. Financial Close Evidence Graph.
7. Draft and Approval Review.
8. Knowledge Library.
9. Administration and Audit.
10. Responsive and accessibility passes.

For every screen request:

- Desktop 1440px.
- Compact desktop 1024px.
- Mobile 390px where applicable.
- Default, loading, empty, error, and permission-denied states.

## Review gate after each screen

- Official logo is unchanged and has sufficient safe area.
- Product name is exactly `Bravo Agent AI`.
- Green remains dominant; orange is not decorative or dominant.
- `//` encodes a real transition, relationship, or verification state.
- No invented financial values, menu paths, versions, schemas, or completion claims.
- Company, period, environment, and version are visible when known.
- Unknown scope is explicit.
- Evidence statuses use text and icon in addition to color.
- Draft, Approved, Executed, and Verified remain separate states.
- Unauthorized navigation, counts, graph nodes, and metadata are absent.
- Keyboard focus and contrast are visible.
- Mobile has no accidental horizontal scrolling.

## Export handoff

1. Select one approved direction and discard inconsistent variations.
2. Normalize typography, spacing, color, radius, and state names.
3. Verify Vietnamese copy and diacritics.
4. Replace invented examples with reviewed fixtures.
5. Capture desktop and mobile screenshots for comparison.
6. Export final frames and components, not early experiments.

