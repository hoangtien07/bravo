# Bravo Agent AI - Product Design Specification

Status: `APPROVED FOR GOOGLE STITCH EXPLORATION`

Brand authority: BRAVO Brand Guidelines Version 1.0 (2015)

Initial product scope: Conversation, Financial Close, Evidence, Approval, Knowledge, and Financial Close Graph.

## 1. Product thesis

Bravo Agent AI is a trusted enterprise ERP advisory workspace for Vietnamese accountants,
chief accountants, finance managers, BRAVO consultants, and authorized administrators.

The first and deepest experience is Financial Close Advisor. The interface must help a user:

- clarify the real accounting outcome;
- identify applicable closing prerequisites;
- distinguish completed, missing, conflicting, inferred, and unverified evidence;
- receive the safest useful next action;
- review citations, scope, and assumptions;
- keep every mutation behind explicit draft and approval controls.

This is not a generic AI chatbot, marketing website, or decorative analytics dashboard.

The visual direction is **Assured Operations - Quản trị chắc chắn, có bằng chứng**. The product
should feel professional, calm, precise, dependable, and quietly optimistic. BRAVO means the
confidence and satisfaction felt after work has been completed correctly.

## 2. Naming and brand architecture

- Official corporate wordmark: `BRAVO`.
- Product name: `Bravo Agent AI`.
- Vietnamese descriptor: `Trợ lý nghiệp vụ có bằng chứng`.
- Do not redraw or insert `Agent AI` into the official BRAVO wordmark.
- In the application header, place the product label beside the official logo as editable text.
- In compact layouts, show the official BRAVO logo and shorten the product label to `Agent AI`.

Recommended interface language:

- Greeting: `Bravo Agent AI có thể hỗ trợ anh/chị kiểm tra công việc nào?`
- Loading: `Bravo Agent AI đang đối chiếu điều kiện và bằng chứng...`
- Evidence gap: `Chưa đủ bằng chứng để xác nhận kết luận này.`
- Draft boundary: `Đây là bản nháp, chưa được thực hiện trên hệ thống.`

## 3. Brand signature

Use BRAVO's paired diagonal `//` motif as the single signature product element.

- Angle: 29 degrees.
- Origin: software comment syntax and the diagonal construction already present in the logo.
- Meaning: BRAVO-customer partnership, explanation, verified progress, and forward movement.
- Use it as a meaningful separator, progress marker, graph edge marker, or evidence-completion cue.
- Do not repeat it as background decoration across every card or page.
- Do not rotate the official logo to imitate the motif.

The product avatar is an abstract mark derived from the paired diagonal strokes. It is not a robot,
brain, face, animal, or cartoon character. Negative space between the strokes may suggest a check
mark or assurance shield. The avatar and official BRAVO logo remain separate assets.

## 4. Logo rules

- Use the official supplied PNG for digital interfaces.
- Prefer the official green logo on white or very light neutral backgrounds.
- Preserve the official safe area around the logo.
- Never stretch, compress, crop, rotate, outline, recolor, or add shadow to the logo.
- Never place the green logo directly on unrelated colored backgrounds.
- Use an approved positive/negative version if a dark background is later introduced.
- Do not use legacy ISO lockups as the product logo.

## 5. Color system

### Official brand colors

| Token | Hex | Role |
|---|---|---|
| BRAVO Green | `#00A88D` | Logo, large brand surfaces, verified accents |
| BRAVO Orange | `#FBAF3F` | Attention, pending evidence, milestone highlight |
| BRAVO Dark Gray | `#6D6E70` | Secondary brand copy |
| BRAVO Light Gray | `#BBBDC0` | Supporting neutral |
| White | `#FFFFFF` | Primary surface |

### Accessible digital extensions

| Token | Hex | Role |
|---|---|---|
| Interactive Teal | `#006B5D` | Primary button, link, keyboard focus |
| Interactive Hover | `#00574C` | Hover/pressed state |
| Soft Teal | `#E8F7F4` | Selected and verified surface |
| Canvas | `#F6F9F8` | Application background |
| Strong Text | `#1F2927` | Main content |
| Secondary Text | `#56625F` | Metadata and helper copy |
| Border | `#D7E1DE` | Dividers and component borders |
| Warning Surface | `#FFF4DE` | Missing/pending evidence surface |
| Error | `#B42318` | Confirmed conflict or blocking failure |
| Error Surface | `#FDECEA` | Conflict background |
| Information | `#175CD3` | Neutral information requiring distinction |

Rules:

- Green is the dominant brand color.
- Orange must remain below 50% of a composition and never dominate the interface.
- Do not use orange for long text, white-on-orange primary buttons, or decoration without meaning.
- Use `#006B5D`, not `#00A88D`, when white text or small interactive text requires stronger contrast.
- Never use generic purple AI gradients, neon glows, cream/terracotta palettes, or glassmorphism.
- Status is always communicated by label and icon, never by color alone.

## 6. Typography

Primary UI stack:

```css
-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Arial, sans-serif
```

Roles:

| Role | Size/line | Weight |
|---|---:|---:|
| Page title | 28/34 | Semibold |
| Section title | 20/28 | Semibold |
| Card title | 16/24 | Semibold |
| Body | 14/22 | Regular |
| Compact UI | 13/18 | Medium |
| Evidence metadata | 12/18 | Medium |
| Financial data | 14/20 | Medium, tabular numerals |

- Use sentence case.
- Use uppercase only for very short governed status labels.
- Use tabular numerals for financial values, dates, versions, counts, and reconciliation results.
- Do not introduce a decorative serif or futuristic display font.

## 7. Layout system

- Desktop-first target: 1280-1600px.
- Compact desktop: 1024px.
- Tablet: 768px.
- Mobile conversation support: 390px.
- Base spacing unit: 4px.
- Content rhythm: 8 / 12 / 16 / 24 / 32px.
- Sidebar: 264px expanded, 72px collapsed.
- Evidence/detail panel: 360-400px.
- Readable answer width: 760-840px.
- Card radius: 8px.
- Button/input radius: 6px.
- Prefer subtle borders over shadows.
- Avoid excessive floating cards, nested cards, and pill-shaped controls.

Desktop shell:

```text
+----------------------+--------------------------------------+--------------------+
| BRAVO  Agent AI      | Task title + company/period/version  | Evidence status    |
| New conversation     +--------------------------------------+--------------------+
| Financial Close      |                                                           |
| Conversations        | Conversation / readiness / graph workspace                |
| Knowledge            |                                                           |
| Approvals            |                                                           |
| Administration       |                                                           |
|                      |                                                           |
| User + environment   |                                                           |
+----------------------+-----------------------------------------------------------+
```

The shell must display company, branch, accounting period, and BRAVO version when known. Unknown
scope is explicitly labeled; it is never silently invented.

## 8. Navigation and initial scope

Primary navigation:

1. New conversation
2. Financial Close
3. Conversations
4. Knowledge
5. Approvals
6. Administration - only when authorized

The initial V2 dogfood hides Money Engine, Anomaly, Tax, and unrelated legacy surfaces. Graph is
included only as a Financial Close evidence/prerequisite view. Authorization is applied before
navigation, counts, graph data, or content reaches the UI.

## 9. Core screens

### 9.1 Sign in

Single job: authenticate the user and establish the trusted environment.

- Restrained two-column desktop composition.
- Left: official logo, product thesis, one purposeful `//` motif.
- Right: compact authentication panel.
- Primary SSO action when enabled.
- Email/password appears only when the environment permits it.
- Show environment/support information below the form.
- No stock photography or generic AI illustration.

### 9.2 New conversation

Single job: begin a useful BRAVO task.

- Role-aware greeting.
- Prominent composer with attachment and profile set to Auto.
- Four realistic Financial Close task starters.
- Recent conversations below the composer.
- Visible statement that exact claims require evidence and all actions remain draft-only.

Task starters:

- `Kiểm tra mức độ sẵn sàng đóng kỳ tháng 06/2026`
- `Tôi còn thiếu bước nào trước khi lập báo cáo tài chính?`
- `Đối chiếu các chênh lệch công nợ cuối kỳ`
- `Tổng hợp bằng chứng để bàn giao cho kế toán trưởng`

### 9.3 Active advisory conversation

- Left navigation/history, center conversation, optional right evidence drawer.
- Answers are organized naturally around outcome, applicable prerequisites, next action,
  uncertainty, and one high-information clarification when necessary.
- Do not expose chain-of-thought or mechanical agent steps.
- Composer supports files/images, stop generation, task scope, and draft-only indicator.
- Streaming must not cause horizontal movement or layout jumping.

### 9.4 Financial Close readiness

Use the signature Evidence Rail `//` to show this governed flow:

1. Scope and reporting period
2. Source documents posted
3. Subledgers reconciled
4. Applicable period processes
5. Period-end entries
6. Closing controls
7. Report mappings and opening balances
8. Reports and variance review

Each node shows one state:

- Not assessed
- Missing evidence
- In progress
- Ready
- Conflict
- Not applicable

Every readiness status must expose its reason and evidence. Do not reduce readiness to an
unexplained percentage, speedometer, or donut chart.

### 9.5 Evidence drawer

For each claim show:

- claim summary;
- source name;
- document page, cell, or data scope;
- company, period, environment, and BRAVO version;
- evidence status;
- effective/approval status;
- conflict or missing-data warning.

Clearly distinguish user-supplied, verified, inferred, conflicting, and missing facts. Citations
open the matching evidence without losing the user's conversation position.

### 9.6 Draft and approval review

Every mutation is visibly a draft.

- Proposed change and business purpose.
- Affected scope.
- Before/after comparison.
- Evidence and validation status.
- Risk and missing checks.
- Approve, Request changes, and Reject actions.
- Audit trail.

Never represent Approved as Executed or Verified.

### 9.7 Knowledge library

Show governed documents and evidence packs with owner, BRAVO version, effective date, approval
status, visibility scope, ingestion status, page/cell traceability, and superseded/conflicting
warnings.

### 9.8 Financial Close Evidence Graph

The graph is a governed, stable, left-to-right dependency map. It is not a decorative
force-directed network.

```text
Reporting outcome
  -> prerequisite groups
  -> BRAVO operation or control
  -> evidence and verification result
```

Node types:

- Outcome
- Business prerequisite
- BRAVO operation/control
- Evidence
- Conflict
- Missing information

Interactions:

- Selecting a node opens a right-side detail inspector.
- The inspector shows reason, evidence, environment/version, period, and responsible role.
- Selecting a conversation citation focuses the matching graph node.
- Selecting a graph node can open the matching conversational explanation.
- Filters: milestone, status, evidence type, accounting period, responsible role.
- Controls: search, zoom, fit selection, reset view, and accessible list view.
- Preserve a curated layout; nodes must not continuously rearrange themselves.

Security:

- Authorization is enforced before graph data reaches the UI.
- Never reveal unauthorized node labels, counts, edges, or aggregate metadata.
- Use a neutral permission boundary if part of a path is unavailable.

Visual rules:

- Paired 29-degree `//` marks may become directional edge markers.
- Green indicates a verified path.
- Orange indicates pending attention or missing evidence.
- Red is reserved for confirmed conflict or a blocked safety condition.
- Avoid glowing nodes, particle effects, and AI-brain imagery.

### 9.9 Administration and audit

Role-gated workspace for identity/scope, runtime policy, controlled cloud egress, corpus governance,
audit events, failed safety checks, and system health. Security state must be understandable without
exposing secrets.

## 10. Components and states

Design every relevant component in:

- default;
- hover;
- keyboard focus;
- disabled;
- loading;
- empty;
- error;
- success;
- permission denied;
- stale evidence;
- conflicting evidence;
- offline or limited capability.

Use skeletons only where content shape is stable. Errors state what failed and the next corrective
action. Empty states invite a relevant action.

## 11. Motion

- 120-180ms for hover and panel transitions.
- The paired `//` advances once when a prerequisite becomes verified.
- No ambient animation, floating objects, animated particles, or continuous gradients.
- Honor `prefers-reduced-motion`.

## 12. Accessibility

- WCAG 2.2 AA contrast.
- Minimum 44px touch target on mobile.
- Fully visible keyboard focus.
- Semantic headings, forms, tables, and dialog labels.
- Correct focus management for evidence drawers and dialogs.
- Graph has an equivalent hierarchical list/table representation.
- Keyboard users traverse graph nodes in logical dependency order.
- Conversation remains usable at 200% zoom.

## 13. Content style

Vietnamese-first. Use direct, professional, user-centered language.

- `Lưu thay đổi`, not `Gửi`.
- `Yêu cầu bổ sung`, not `Xử lý`.
- `Thiếu bằng chứng đối chiếu công nợ`, not `Dữ liệu chưa hợp lệ`.
- `Bản nháp đã được phê duyệt`, not `Đã hoàn tất`.

Do not make unsupported claims such as `đã kiểm tra`, `đã thực hiện`, or `số liệu chính xác` without
matching evidence.

## 14. Explicitly avoid

- Generic AI chat visual language.
- Purple/blue neon gradients.
- Glassmorphism.
- Excessive rounded cards and pills.
- Decorative KPI hero numbers.
- Fake charts or financial amounts.
- Robots, brains, faces, animals, and sparkle illustrations.
- Decorative citations.
- Unexplained readiness percentages.
- Presenting a proposed or approved action as executed.
- Exposing hidden modules, records, graph nodes, edges, or counts.
