# Audit Figma Make UI theo Frontier Product Delivery

Ngày đánh giá: 2026-07-20  
Phạm vi: `FigmaMake_UI`, `frontend-react`, API/backend hiện tại và các guardrail Conversation Core V2.  
Baseline: branch `feat/v2-p0-containment`, commit `f17d31c079f8de71f0ffc303495f3176eef59d23`, Alembic head `0017_native_rls_backstop`.

## 1. Kết luận điều hành

`FigmaMake_UI` hiện là **high-fidelity interactive prototype**, chưa phải frontend có thể đưa vào sản phẩm hoặc thay trực tiếp `frontend-react`.

Thiết kế mới có chất lượng thị giác và kiến trúc thông tin tốt hơn rõ rệt ở desktop. Nó nên trở thành **visual target + source cho design system và component composition** của BRAVO V2. Không nên thay nguyên frontend hiện tại bằng source Figma Make, vì source này chưa có auth thật, route thật, API, SSE, RLS-aware navigation, persistence, error model, test, responsive implementation hoặc domain contracts tương ứng.

Khuyến nghị: **giữ nền tảng runtime của `frontend-react`, đưa ngôn ngữ thiết kế Figma Make vào theo strangler vertical slice Financial Close Advisor**. Không fork thành một app sản phẩm thứ hai và không port toàn bộ feature parity của legacy UI.

## 2. Verdict theo gate

| Gate | Trạng thái | Nhận định |
|---|---|---|
| Visual direction / brand | PASS | BRAVO green, typography, density, `//` motif và hierarchy phù hợp sản phẩm ERP nội bộ |
| Desktop usability 1440px | PASS có điều kiện | Các màn hình Sign in, Conversation, Readiness, Graph và Approval rõ, nhất quán |
| Compact desktop 1024px | FAIL | Graph bị cắt node kết quả; shell cố định 264px không co giãn đúng |
| Mobile 390px | FAIL nghiêm trọng | Sidebar vẫn 264px; workspace còn khoảng 126px và nội dung bị clip |
| Real authentication / authorization | FAIL | “Đăng nhập” chỉ đổi React state; menu admin luôn render |
| API / BE integration | FAIL | Không có `fetch`, API client, SSE hay persistence trong `FigmaMake_UI/src` |
| Evidence integrity | FAIL nghiêm trọng | Prototype hard-code số tiền, công ty, phiên bản, trang/sheet và trạng thái verified/approved |
| Draft / approval safety | FAIL | Nút approve/reject chỉ đổi local state; không enforce permission, maker-checker hoặc DB state |
| BA state coverage | FAIL | Plan hứa loading/empty/error/permission/offline/stale nhưng source gần như chỉ có happy-path demo |
| Accessibility | PARTIAL | Có global `:focus-visible` và reduced motion; thiếu responsive, focus management, live regions và graph list equivalent |
| Build portability | FAIL có thể sửa nhỏ | Export thiếu `.figma/make/site.json`; build mặc định không chạy ngoài Figma Make |
| Automated verification | FAIL | Không có test script hoặc test file trong app Figma Make |
| Productization feasibility | YES | Khả thi nếu tái sử dụng design, không tái sử dụng app shell/runtime nguyên trạng |

## 3. Bằng chứng chính

### P0 — prototype trình bày dữ liệu giả như sự thật đã xác minh

- Conversation hard-code kết luận, nguồn, trang/sheet, công ty, kỳ, phiên bản và chênh lệch `12.500.000 VND` trong `FigmaMake_UI/src/components/ActiveConversation.tsx:33-65`.
- Readiness hard-code `127/130`, số tiền chênh lệch, trạng thái ready/conflict và nghiệp vụ đã hoàn thành trong `FigmaMake_UI/src/components/FinancialCloseReadiness.tsx:19-96`.
- Graph hard-code các node “Đã xác minh”, “Đã hoàn thành”, `127 chứng từ`, số tiền và `v2.x` trong `FigmaMake_UI/src/components/FinancialCloseGraph.tsx:26-52`.
- Approval hard-code tỷ lệ 3%, số dư trước/sau và tài khoản trong `FigmaMake_UI/src/components/DraftApproval.tsx:20-52`.

Điều này vi phạm trực tiếp invariant “exact financial/schema/version/execution claims require matching evidence” và cũng trái với chính `FigmaMake_UI/src/imports/DESIGN.md`.

### P0 — không có trusted platform shell

- Auth chỉ là `useState(false)` rồi `setAuthenticated(true)` tại `FigmaMake_UI/src/App.tsx:13-18`.
- Nút SSO gọi thẳng `onSignIn` tại `FigmaMake_UI/src/components/SignIn.tsx:75-79`.
- Navigation khai báo `adminOnly` nhưng không hề lọc theo identity/permissions tại `FigmaMake_UI/src/components/AppShell.tsx:13-20` và `:49-76`.
- Không có API call trong `FigmaMake_UI/src`; chat response được mô phỏng bằng `setInterval` tại `ActiveConversation.tsx:81-101`.
- Approve/request changes/reject chỉ cập nhật state cục bộ tại `DraftApproval.tsx:60-69` và `:173-181`.

### P1 — responsive implementation chưa tồn tại

- CSS chỉ có reduced-motion media query, không có breakpoint/layout adaptation: `FigmaMake_UI/src/index.css:45-55`.
- Shell dùng sidebar cố định 264px và full viewport: `AppShell.tsx:23-30`.
- Browser audit tại 390×844 đo được main workspace chỉ còn khoảng 126px; màn hình Financial Close bị clip gần như toàn bộ.
- Browser audit tại 1024×768 cho thấy Financial Close Graph cắt node outcome bên phải.

### P1 — BA coverage mới nằm trong tài liệu, chưa nằm trong sản phẩm

Plan yêu cầu default/loading/empty/error/permission-denied/offline và mobile, nhưng source không có state machine hoặc fixture switch để kiểm chứng. `SkeletonRow` được định nghĩa tại `shared.tsx:76-80` nhưng không được dùng trong màn hình. Không có permission-denied view, offline capability state, stale evidence flow, dialog focus management hoặc recovery action thật.

### P1 — graph chưa đạt contract đã mô tả

Graph desktop có bố cục trái-sang-phải tốt, nhưng mới chỉ có 4 filter trạng thái. Thiếu search, milestone/evidence/period/role filters, zoom, fit, reset, accessible hierarchical list, citation-to-node và node-to-conversation linking. Backend `/api/graph` hiện là semantic source graph, không phải Financial Close prerequisite/evidence graph (`app/api/routes_graph.py:1-7`, `:51-70`).

### P1 — draft UI giàu hơn contract backend hiện tại

UI mới cần purpose, affected scope, before/after, validation, risk, missing checks, requester/reviewer, audit trail và bốn trạng thái Draft/Approved/Executed/Verified. `DraftOut` hiện chỉ trả id/kind/status/payload/creator/time (`app/api/routes_drafts.py:26-47`) và API chỉ hỗ trợ approve/reject (`:143-162`). Chưa có request-changes transition, revision/CAS, validation report, review note/audit trail read model, executed hoặc verified state.

### P2 — build và maintainability

- Build mặc định fail vì import file export-specific bị thiếu tại `FigmaMake_UI/vite.config.ts:6`.
- Source component tự thân type-check được khi loại config Figma khỏi compile; build audit tối thiểu thành công với bundle JS khoảng 261 kB.
- Inline styles chiếm gần toàn bộ UI, làm responsive/theming/state variants khó bảo trì.
- Console ghi nhận React warning do trộn `borderLeft` shorthand với longhand trong `AppShell.tsx:57-65`.
- React 19/Tailwind 4/Vite 8 khác stack hiện tại React 18/Tailwind 3/Vite 5; nâng stack không tạo giá trị nghiệp vụ cho vertical slice và tăng rủi ro migration.

## 4. Những gì nên giữ

| Asset từ Figma Make | Quyết định | Cách dùng |
|---|---|---|
| Brand palette + semantic colors | ADOPT | Chuyển thành token có kiểm tra contrast trong frontend hiện tại |
| Typography, spacing, border/radius discipline | ADOPT | Chuẩn hóa vào primitives hiện có, bỏ inline style |
| `//` motif | ADOPT | Một signature có nghĩa cho evidence/progress/edges |
| App shell visual composition | ADAPT | Giữ React Router, auth store, permission guards của frontend hiện tại |
| New conversation composition | ADAPT | Nối conversation store, attachments, profile và real recent conversations |
| Conversation + evidence drawer | ADOPT/ADAPT | Nối SSE hiện tại; cần Evidence/Claim read model mới |
| Financial Close Evidence Rail | ADOPT cho V2 slice | Nối typed prerequisite/readiness endpoint; không dùng fixture hard-code |
| Financial Close Graph | REDESIGN implementation | Giữ visual grammar, xây graph từ governed read model và có list equivalent |
| Draft review layout | ADAPT | Chỉ bật field/action được backend contract và permission chứng minh |
| Knowledge Library layout | ADAPT | Cần mở rộng Source governance metadata trước |
| Source app state/router/auth simulation | REMOVE | Không đưa vào product code |
| Hard-coded financial/evidence fixtures | REMOVE khỏi runtime | Chỉ giữ trong Storybook/test fixtures, gắn nhãn synthetic rõ ràng |

## 5. FE–BE–BA contract map

| Surface | Năng lực hiện có có thể giữ | Gap cần đóng trước khi gọi là thật |
|---|---|---|
| Sign in / shell | `/api/auth/login`, `/api/me`, `useAuth`, Protected routes | OIDC/SSO wiring, permission-filtered nav, environment/context endpoint |
| Conversation | `/api/chat/{id}/messages` SSE, abort, attachments, conversations, feedback | Typed TaskBrief, claim/evidence projection, uncertainty/status contract |
| Recent conversations | `/api/conversations` CRUD/share/truncate | Map title/task epoch/status; không dùng sample history |
| Financial Close readiness | Consultant TaskState + workflow catalog là nền sơ bộ | Endpoint riêng trả prerequisite node, applicability, reason, evidence refs, revision và scope |
| Evidence drawer | SSE hiện có trả citation strings | EvidenceClaim DTO cần source locator, scope, provenance class, approval/effective/stale/conflict status |
| Close graph | `/api/graph` có RLS nhưng sai domain | Financial Close dependency graph read model, authorization trước serialization |
| Draft approval | Draft list/get/approve/reject có permission + maker-checker | Rich review projection, request-changes, audit trail, validation, revision, lifecycle states |
| Knowledge library | `/api/sources` có visibility và owner-scope | owner display, BRAVO version, effective date, approval, supersession, conflict, traceability |
| Administration | User/dept/usage/feedback endpoints | Runtime/egress/corpus/audit/health read models và role gates |

## 6. Target architecture

```text
Figma Make visual language
          |
          v
frontend-react primitives + feature modules
React Router | auth store | API client | SSE | accessibility | tests
          |
          v
Existing trusted platform shell
Auth/RLS | conversation ownership | evidence | drafts/approval | audit
          |
          v
New Financial Close V2 read models
TaskBrief | PrerequisitePlan | EvidenceBundle | ReadinessProjection | StateDelta
```

Không tạo một frontend sản phẩm độc lập trong `FigmaMake_UI`. Thư mục này nên trở thành design-reference/prototype fixture; code sản phẩm tiếp tục ở `frontend-react`.

## 7. Lộ trình chuyển đổi đề xuất

### Wave 0 — freeze và contract

1. Chụp/freeze các frame 1440/1024/390 đã duyệt; loại toàn bộ invented claims khỏi runtime demo.
2. Viết FE contract fixtures cho scope, readiness nodes, claim evidence, conflicts, permission boundary và draft lifecycle.
3. Chốt endpoint/read-model schema trước khi viết lại component.
4. Giữ System A/B conversation outputs đóng băng; UI migration không được thay prompt/routing/synthesis.

### Wave 1 — design system trong frontend hiện tại

1. Port token, typography, density, focus style và `//` motif.
2. Port shell visual nhưng giữ router/auth/API stores.
3. Bổ sung responsive shell: desktop sidebar, compact collapse, mobile drawer/bottom-safe composer.
4. Thêm Storybook hoặc fixture harness cho mọi state BA bắt buộc.

### Wave 2 — canonical conversation wedge

1. Port New Conversation và Active Conversation.
2. Giữ SSE/abort/upload/feedback/share hiện có.
3. Thêm Evidence drawer qua DTO mới; fail closed khi locator/version/scope thiếu.
4. Ẩn Money Engine/Anomaly/Tax/legacy graph trong dogfood V2 theo handoff plan.

### Wave 3 — Financial Close deep slice

1. Xây readiness endpoint và projection từ typed domain state.
2. Port Evidence Rail; mỗi status phải có reason + evidence + scope + revision.
3. Xây graph domain riêng, permission-filter trước serialization, có accessible list equivalent.
4. Port draft review sau khi backend có rich lifecycle contract.

### Wave 4 — evidence-based release

1. Visual regression 1440/1024/390, 200% zoom, keyboard-only và reduced motion.
2. Contract tests FE–BE, two-user/two-department negative probes và no-hidden-count checks.
3. E2E cho auth expiry, SSE error/cancel, stale revision, missing/conflicting evidence, approve/reject/request-changes.
4. Tách riêng đánh giá UI usability khỏi A/B/C/D conversation-quality verdict.

## 8. Acceptance gates trước khi chuyển traffic

- Không có dữ liệu tài chính/version/schema/verified hard-code trong production bundle.
- Navigation và mọi count/detail đều permission-filtered từ server.
- Financial Close state có scope công ty/chi nhánh/kỳ/version rõ hoặc explicit unknown.
- Mọi readiness conclusion có reason và evidence refs; unsupported exact claim fail closed.
- Draft, Approved, Executed và Verified là bốn state khác nhau trong domain/backend/UI.
- 390px không clip nội dung; mobile target tối thiểu 44px; 1024px không mất graph node/action.
- Graph có keyboard order và equivalent list view.
- Loading, empty, error, permission denied, stale, conflict, offline/limited capability đều có test.
- Existing FE typecheck/tests và security-critical backend integration tests vẫn xanh.

## 9. Verification đã chạy

- Baseline commit và Alembic head đã ghi nhận; `FigmaMake_UI/` vốn là untracked user content.
- `frontend-react`: TypeScript no-emit pass; 3 test files / 7 tests pass.
- `FigmaMake_UI`: dependency lock cài được; source TSX type-check pass khi tách khỏi config export lỗi.
- Build mặc định fail do thiếu `.figma/make/site.json`; build audit bằng config Vite tối thiểu pass.
- Browser audit: Sign in, New Conversation, Conversation/Evidence, Readiness, Graph, Approval tại 1440px; Graph tại 1024px; Financial Close và shell tại 390px.

## 10. Quyết định đề xuất

**GO có điều kiện cho việc chuyển đổi design; NO-GO cho việc thay nguyên frontend bằng source Figma Make hiện tại.**

Thử nghiệm nhỏ nhất có giá trị: port design tokens + responsive shell + New/Active Conversation vào một feature flag trong `frontend-react`, giữ toàn bộ auth/API/SSE hiện có; dùng synthetic contract fixtures không có exact claims. Chỉ sau khi slice này qua responsive, accessibility và contract tests mới triển khai Readiness/Graph với backend V2 read models.
