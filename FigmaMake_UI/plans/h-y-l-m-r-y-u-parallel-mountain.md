# Plan: Bravo Agent AI – Chatbot + Agent UI

## Context

The user wants to build the Bravo Agent AI application from the detailed design specification in `src/imports/DESIGN.md`. This is a Vietnamese enterprise ERP advisory workspace for accountants, with a focus on Financial Close workflows. The existing codebase is a blank Vite + React + Tailwind v4 project with only a placeholder dot-grid `App.tsx`.

The request is to implement the complete chatbot + AI Agent UI according to the spec, brand guidelines, and Vietnamese-first content.

---

## Architecture

Single-file `src/App.tsx` replaced with a multi-screen SPA using React `useState` for routing (no router library needed at this scale). Components split into separate files under `src/components/`.

**Screens (implemented as views):**
1. `SignIn` – two-column auth screen
2. `NewConversation` – role-aware greeting + composer + starters
3. `ActiveConversation` – left nav / center chat / right evidence drawer
4. `FinancialCloseReadiness` – Evidence Rail with `//` motif
5. `FinancialCloseGraph` – stable left-to-right dependency map (static layout)
6. `DraftApproval` – draft/approval review queue
7. `KnowledgeLibrary` – governed document list

**Shell:** `AppShell` wraps screens 2–7 with 264px collapsible sidebar + context header.

---

## Files to create / modify

| File | Action |
|---|---|
| `src/App.tsx` | Replace – top-level router/state |
| `src/index.css` | Extend – add CSS variables for brand tokens |
| `src/components/SignIn.tsx` | Create |
| `src/components/AppShell.tsx` | Create |
| `src/components/NewConversation.tsx` | Create |
| `src/components/ActiveConversation.tsx` | Create |
| `src/components/EvidenceDrawer.tsx` | Create |
| `src/components/FinancialCloseReadiness.tsx` | Create |
| `src/components/FinancialCloseGraph.tsx` | Create |
| `src/components/DraftApproval.tsx` | Create |
| `src/components/KnowledgeLibrary.tsx` | Create |
| `src/components/shared.tsx` | Create – DiagonalMotif, StatusBadge, SkeletonRow |

---

## Design tokens (CSS variables in `src/index.css`)

```css
--color-brand-green: #00A88D;
--color-interactive: #006B5D;
--color-interactive-hover: #00574C;
--color-soft-teal: #E8F7F4;
--color-canvas: #F6F9F8;
--color-strong-text: #1F2927;
--color-secondary-text: #56625F;
--color-border: #D7E1DE;
--color-orange: #FBAF3F;
--color-warning-surface: #FFF4DE;
--color-error: #B42318;
--color-error-surface: #FDECEA;
--color-information: #175CD3;
```

Font: system stack `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Arial, sans-serif`

---

## Key implementation notes

### `//` motif
SVG element: two parallel lines at 29°, color varies by context (green=verified, orange=pending, gray=neutral). Used as:
- Left panel separator on SignIn
- Evidence Rail progress marker
- Graph edge directional marker

### Logo
Use `<img src="/src/imports/bravo-logo.png" />` — never alter dimensions/colors. Product label `Agent AI` as sibling `<span>`.

### Evidence states
`StatusBadge` component: icon + text label + color. States: `not-assessed`, `missing`, `in-progress`, `ready`, `conflict`, `not-applicable`. Color is never the sole indicator.

### Chat streaming
Simulate streaming with `useEffect` + interval to append text progressively. No layout shift — pre-allocate width.

### Draft boundary
Every AI-generated mutation shows a yellow `[NHÁP]` pill. Approval actions show Approve / Request changes / Reject.

---

## Scope for this build

Priority order matching STITCH-SCREEN-PROMPTS.md:
1. SignIn + AppShell (sidebar + header)
2. NewConversation
3. ActiveConversation + EvidenceDrawer
4. FinancialCloseReadiness
5. FinancialCloseGraph (static layout)
6. DraftApproval
7. KnowledgeLibrary

All screens get: default, loading skeleton, empty, and error states. Mobile (390px) supported via responsive Tailwind classes. Vietnamese copy throughout.

---

## Verification

1. Dev server is always running at `$PORT` — preview in Figma Make panel
2. Navigate through all screens via sidebar
3. Check: logo unchanged, green dominant, `//` appears meaningfully, Vietnamese copy correct, no invented financial values, Draft ≠ Approved ≠ Executed
4. Resize to 1024px and 390px to verify responsive behavior
