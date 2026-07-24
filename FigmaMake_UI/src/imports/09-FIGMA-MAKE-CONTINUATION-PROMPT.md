# Prompt tiếp tục hoàn thiện Bravo Agent AI trên Figma Make

Sao chép toàn bộ nội dung trong khối prompt dưới đây vào Figma Make. Đây là continuation brief: sửa và hoàn thiện project hiện tại, không thiết kế lại từ đầu.

---

## MASTER PROMPT

Bạn đang tiếp tục chỉnh sửa project React hiện có của **Bravo Agent AI** trong Figma Make.

Hãy làm việc như một Principal Product Designer và Design Engineer chuyên sản phẩm ERP/kế toán doanh nghiệp. Mục tiêu của vòng này là đưa giao diện hiện tại từ một high-fidelity prototype đẹp thành một **design-complete, product-logic-correct, responsive, accessible, state-complete interactive prototype**. Chưa nối backend hoặc gọi API ở vòng này; logic sản phẩm phải được thể hiện bằng typed deterministic local state để đóng vai trò executable UX specification.

### 1. Đọc và tuân thủ nguồn thiết kế

Trước khi sửa, hãy đọc đầy đủ:

1. `src/imports/DESIGN.md`
2. `src/imports/STITCH-SCREEN-PROMPTS.md`
3. `plans/h-y-l-m-r-y-u-parallel-mountain.md`
4. `AGENTS.md`

Giữ nguyên các quyết định tốt đang có:

- Visual direction: **Assured Operations — Quản trị chắc chắn, có bằng chứng**.
- Official BRAVO logo không được chỉnh sửa, crop, recolor, stretch hoặc redraw.
- BRAVO green là màu thương hiệu chính; orange chỉ dùng cho attention/pending.
- Paired `//` 29-degree motif là signature duy nhất, chỉ dùng khi nó biểu thị evidence, progress, dependency hoặc verified transition.
- Giao diện bình tĩnh, chính xác, professional, có mật độ phù hợp ERP nội bộ.
- Giữ typography system hiện tại; không thêm serif trang trí hoặc font “AI/futuristic”.
- Không dùng purple gradient, neon, glassmorphism, robot, brain, sparkle, floating decoration, fake KPI dashboard hoặc card bo tròn quá mức.

Không thiết kế lại từ đầu. Hãy nâng cấp direction hiện tại và giữ cảm giác mà các màn hình desktop hiện có đã tạo ra.

### 2. Ranh giới của vòng này

Vòng này chỉ làm **design + frontend interaction prototype**:

- Không gọi `fetch`, Axios, WebSocket, SSE hoặc bất kỳ network API nào.
- Không tạo backend giả, database giả, auth giả có vẻ như bảo mật thật hoặc server mock.
- Không thay đổi logic/backend của dự án BRAVO bên ngoài thư mục này.
- Không tự chọn framework/runtime mới.
- Không thêm dependency nếu có thể thực hiện bằng React, CSS và Tailwind hiện có.
- Không triển khai hành động tài chính thật.
- Các nút mutation như Approve/Reject/Request changes chỉ được mô phỏng chuyển visual state trong prototype.
- Tổ chức UI qua typed props, component variants và fixture adapters để sau này có thể thay fixture bằng API mà không viết lại presentation components.

Tuy chưa nối API, prototype **không được chỉ là tập hợp màn hình tĩnh**. Hãy triển khai một deterministic local product-state model bằng typed state + reducer/state machine để các màn hình, trạng thái và transition phản ánh đúng logic sản phẩm BRAVO. Local state này chỉ là executable UX specification, không giả làm backend và không được tuyên bố là security enforcement thật.

### 2A. Logic sản phẩm BRAVO phải được sửa đúng trong prototype

#### A. Product boundary và navigation

Đây là **Conversation Core V2 nằm sau trusted platform shell**, không phải một bộ dashboard tính năng rời rạc.

Initial dogfood scope:

- một canonical conversation surface;
- một deep vertical slice: **Financial Close Advisor**;
- Evidence, Knowledge và Approval là supporting surfaces;
- Administration chỉ dành cho authorized administrator fixture;
- Financial Close Graph chỉ là một view của prerequisite/evidence model, không phải generic knowledge graph.

Ẩn khỏi primary navigation trong V2 dogfood:

- Money Engine;
- Anomaly;
- Tax;
- generic knowledge graph;
- các legacy feature không phục vụ Financial Close Advisor.

Không thêm feature mới ngoài scope trên. Người dùng bắt đầu từ outcome/task, không bắt đầu từ danh sách công cụ kỹ thuật.

#### B. Canonical task model

Prototype cần typed local models tương đương các khái niệm sau, nhưng không phụ thuộc framework/backend:

```ts
type TaskStatus = "scoping" | "active" | "paused" | "completed" | "cancelled";

type EnvironmentScope = {
  company: KnownOrUnknown;
  branch: KnownOrUnknown;
  accountingPeriod: KnownOrUnknown;
  bravoVersion: KnownOrUnknown;
  environment: KnownOrUnknown;
};

type TaskBrief = {
  taskId: string;
  taskEpoch: number;
  outcome: string;
  profile: "auto" | "business" | "technical";
  status: TaskStatus;
  scope: EnvironmentScope;
  constraints: string[];
  knownFacts: FactRef[];
  missingFacts: MissingFact[];
  risk: "low" | "medium" | "high";
  revision: number;
};
```

Product behavior:

- New Conversation bắt đầu ở `scoping`, không tự giả định Financial Close nếu intent chưa rõ.
- Khi outcome rõ là đóng kỳ/lập BCTC, route sang Financial Close Advisor và tạo prerequisite plan.
- Nếu company/period/environment ảnh hưởng đáng kể tới hướng xử lý, hỏi **một câu hỏi có information gain cao nhất**, không mở form dài bắt người dùng điền tất cả.
- Unknown scope phải được giữ là unknown; không tự điền fixture vào product-default view.
- Khi người dùng đổi mục tiêu thật sự, tăng `taskEpoch`, giữ task cũ trong lịch sử và không để facts của task cũ rò sang task mới.
- Correction cập nhật fact/scope và tăng `revision`; UI phải cho thấy điều gì vừa được sửa và phần đánh giá nào cần tính lại.
- Pause giữ trạng thái để tiếp tục sau; Cancel đóng task nhưng không xóa lịch sử/audit UI.
- Completed chỉ có nghĩa workflow tư vấn đã kết thúc theo acceptance signal, không có nghĩa ERP mutation đã executed hoặc verified.

#### C. Profile/routing logic

Profiles hiển thị cho prototype:

- `Auto`: mặc định; hệ thống chọn profile phù hợp và hiển thị lựa chọn hiện tại.
- `Nghiệp vụ`: outcome, accounting prerequisites, BRAVO operations ở mức đã có evidence.
- `Kỹ thuật`: requirement/schema/config/troubleshooting; exact facts phải có verified evidence.

Không hiển thị ISMS trong product navigation/default selector vì chưa có governed corpus. Nếu cần trong QA mode, hiển thị disabled với lý do `Chưa có kho chính sách được phê duyệt`.

Đổi profile chỉ đổi reasoning/evidence emphasis trong prototype, **không bao giờ đổi permission hoặc làm lộ dữ liệu**.

#### D. Financial Close prerequisite logic

Khi TaskBrief đã route vào Financial Close Advisor, tạo một typed `PrerequisitePlan` với tám group canonical:

1. Scope and reporting period
2. Source documents posted
3. Subledgers reconciled with general ledger
4. Applicable period processes
5. Period-end entries
6. Closing controls
7. Report mappings and opening balances
8. Reports and variance review

Mỗi node cần:

```ts
type PrerequisiteNode = {
  id: string;
  title: string;
  prerequisiteIds: string[];
  applicability: "unknown" | "applicable" | "not_applicable";
  status: "not_assessed" | "missing_evidence" | "in_progress" | "ready" | "conflict" | "not_applicable";
  reason: string;
  evidenceRefs: string[];
  missingEvidence: string[];
  responsibleRole?: string;
  nextSafeAction?: string;
  completionSignal?: string;
};
```

Transition rules:

- Node sau không tự thành `ready` chỉ vì người dùng click hoặc node trước đổi màu.
- `ready` yêu cầu completion signal + evidence phù hợp trong fixture scenario.
- `not_applicable` cần reason; không dùng để che missing evidence.
- `conflict` chặn mọi conclusion phụ thuộc node đó cho tới khi conflict được resolve hoặc explicitly accepted theo policy fixture.
- Nếu prerequisite upstream chưa đủ, downstream ở `not_assessed` hoặc `blocked`, không giả vờ đã đánh giá.
- Report readiness không được biểu diễn bằng percentage chung thiếu giải thích.
- “Có thể mở màn hình báo cáo” không đồng nghĩa “báo cáo đáng tin cậy”.
- Mỗi status phải trace được về reason + evidence/missing evidence.

#### E. Evidence truth model

Tách rõ các loại fact/evidence:

```ts
type EvidenceClass =
  | "user_supplied"
  | "inferred"
  | "verified"
  | "conflicting"
  | "missing"
  | "stale";

type EvidenceRef = {
  id: string;
  claim: string;
  evidenceClass: EvidenceClass;
  sourceName?: string;
  locator?: string;
  company?: string;
  period?: string;
  environment?: string;
  bravoVersion?: string;
  effectiveStatus?: "unknown" | "candidate" | "approved" | "superseded";
  freshness?: "current" | "stale" | "unknown";
  conflictNote?: string;
};
```

Rules:

- `user_supplied` không tự động trở thành `verified`.
- `inferred` giúp tư vấn điều kiện nhưng không được dùng để khẳng định exact financial/schema/version fact.
- `verified` cần source + locator/scope phù hợp trong scenario.
- `stale` không được dùng như current evidence nếu period/version/effective scope khác.
- `conflicting` phải hiển thị các phía xung đột và next verification step.
- `missing` vẫn cho phép conditional guidance, nhưng không cho phép exact conclusion.
- Citation click focus đúng EvidenceRef; EvidenceRef có thể focus matching prerequisite/graph node bằng shared IDs.
- UI không đánh đồng số lượng citation với chất lượng câu trả lời.

#### F. Conversation response logic

Mỗi assistant response trong prototype phải được tạo từ fixture `AnswerDraft`, không phải string hard-code rải rác:

```ts
type AnswerDraft = {
  understoodOutcome: string;
  applicablePrerequisites: AnswerSection[];
  nextAction: string;
  uncertainty: string[];
  clarification?: string;
  evidenceRefs: string[];
  proposedStateDelta?: StateDelta;
};
```

Thứ tự UX ưu tiên:

1. Xác nhận outcome mà hệ thống đang hiểu.
2. Nêu prerequisite quan trọng và trạng thái có evidence.
3. Đưa ra next useful action an toàn.
4. Nêu uncertainty/consequential gap.
5. Chỉ hỏi một clarification có information gain cao khi cần.

Không hiển thị chain-of-thought, planner internals, tool calls hoặc mechanical agent steps. Có thể hiển thị trạng thái ngắn như `Đang đối chiếu điều kiện và bằng chứng`.

#### G. Cross-screen synchronization

Trong local prototype state, các surface phải đồng bộ bằng ID và revision:

```text
Conversation citation
  <-> EvidenceRef
  <-> Financial Close prerequisite node
  <-> Graph node
  <-> Proposed draft, nếu có
```

- Click citation mở đúng evidence.
- Từ evidence mở đúng prerequisite/graph node.
- Từ graph node quay lại conversational explanation tương ứng.
- Correction làm các view liên quan chuyển sang `stale/reassessing` trước khi có fixture result mới.
- Không để mỗi screen dùng một bộ hard-coded status mâu thuẫn nhau.

#### H. Draft, approval, execution và verification lifecycle

Áp dụng state machine rõ ràng:

```text
proposed_draft
  -> validating
  -> validation_failed | ready_for_review
  -> changes_requested | rejected | approved
  -> exported_for_manual_action (nếu loại draft hỗ trợ)
  -> externally_executed (chỉ khi có bằng chứng ngoài prototype)
  -> verified (chỉ khi có matching verification evidence)
```

Rules:

- Model/user action chỉ tạo proposed draft; không tự approve.
- Maker không tự approve draft của chính mình trong fixture role rules.
- Approve không đồng nghĩa execute.
- Project hiện giữ non-invasive boundary: approved journal draft có thể **export CSV/XLSX để nhập tay**, không tự ghi vào BRAVO ERP.
- Export không đồng nghĩa đã nhập ERP.
- `externally_executed` không được phát sinh chỉ vì click button trong prototype; chỉ preview qua QA fixture được dán nhãn minh họa.
- `verified` cần evidence mới chứng minh kết quả sau thực hiện.
- Request changes cần note bắt buộc và quay lại draft revision mới.
- Stale revision phải chặn approval và yêu cầu reload/review lại.
- Missing critical validation/evidence phải disable approval và giải thích reason.
- Audit trail hiển thị actor role, event, timestamp placeholder và revision; không tự tạo identity thật.

#### I. Authorization và permission boundary trong UX spec

Security thật sẽ được backend/database enforce ở vòng tích hợp sau. Tuy nhiên prototype phải mô tả đúng UX contract:

- Non-admin không thấy Administration nav.
- User không có `draft:approve` không thấy approval count/detail/action.
- Permission denied không được làm lộ title, count, graph node label, hidden edge hoặc aggregate metadata.
- Neutral permission boundary chỉ nói `Một phần đường dẫn không khả dụng theo phạm vi truy cập`, không tiết lộ nội dung bị ẩn.
- Shared conversation là read-only; không hiển thị composer/mutation actions.
- UI role fixtures chỉ để review design, phải có chú thích trong QA mode rằng frontend visibility không thay thế server authorization/RLS.

#### J. Offline và controlled capability logic

Prototype cần phân biệt:

- online/local runtime available;
- offline but local capability available;
- limited capability because a required corpus/tool is unavailable;
- cloud route unavailable/blocked by policy.

Không dùng thông báo chung chung `Mất kết nối` cho mọi trường hợp.

- Nếu local path vẫn dùng được, cho phép conversation tiếp tục và nêu capability bị hạn chế.
- Nếu evidence source chưa available offline, giữ conditional guidance + missing evidence state.
- Không gợi ý gửi dữ liệu nhạy cảm ra cloud.
- Không để capability state thay đổi authorization.

#### K. End-to-end UX scenarios bắt buộc

Design QA mode phải chạy được ít nhất các scenario sau bằng deterministic fixtures:

1. New user, unknown scope → hỏi một clarification về company/period.
2. Financial Close task, scope known, all prerequisites not assessed.
3. Partial evidence → một số node in progress/missing, có next safe action.
4. Conflicting reconciliation evidence → downstream reporting conclusion bị blocked.
5. User corrects accounting period → related evidence/readiness chuyển stale/reassessing và revision tăng.
6. User switches from Financial Close sang technical task → task epoch mới, không kế thừa facts cũ.
7. User pauses rồi resumes task.
8. User cancels task → không còn active composer action cho task đó, history vẫn còn.
9. Draft validation failed → approval disabled, có correction path.
10. Draft approved → vẫn hiển thị `Chưa thực hiện trên BRAVO ERP`.
11. Request changes → bắt buộc note, tạo revision mới.
12. Permission-limited role → không rò approval count, graph labels hoặc admin navigation.
13. Offline/local-capable → vẫn tư vấn giới hạn, không tạo exact claims.
14. Evidence stale/superseded → không dùng làm current verified conclusion.

Mỗi scenario phải điều hướng được qua các screen liên quan và không tạo status mâu thuẫn.

### 3. Sửa vấn đề dữ liệu giả ngay lập tức

Project hiện tại đang hiển thị các con số, tài khoản, tên công ty, kỳ, nguồn, trang/sheet, phiên bản và trạng thái “đã xác minh” như dữ liệu thật. Điều này không được phép.

Hãy loại khỏi runtime demo mọi ví dụ cụ thể kiểu:

- số tiền hoặc tỷ lệ phần trăm;
- số lượng chứng từ đã xử lý;
- tài khoản kế toán cụ thể;
- tên khách hàng/công ty giả có vẻ là dữ liệu thật;
- `v2.x` hoặc một BRAVO version không được cung cấp;
- trang, sheet, cột hoặc locator giả;
- “đã xác minh”, “đã duyệt”, “đã hoàn thành” nếu không được trình bày rõ là fixture minh họa.

Thay bằng một trong hai cách:

1. Trạng thái an toàn mặc định: `Chưa xác định`, `Chưa chọn`, `Chưa có bằng chứng`, `Chưa đánh giá`.
2. Khi cần trình diễn component states trong QA mode, gắn nhãn nổi bật và nhất quán: `DỮ LIỆU MINH HỌA — KHÔNG PHẢI DỮ LIỆU THỰC`.

Ví dụ nội dung an toàn:

- `Có chênh lệch cần giải trình` thay vì một số tiền cụ thể.
- `Nguồn chưa được liên kết` thay vì tự tạo tên tài liệu/trang/sheet.
- `Phiên bản BRAVO chưa xác định` thay vì `v2.x`.
- `Phạm vi công ty và kỳ kế toán chưa được chọn` thay vì giả định scope.
- `Trạng thái minh họa: Sẵn sàng` chỉ xuất hiện trong Design QA mode.

Mọi màn hình product mặc định phải bắt đầu fail-closed và không tạo cảm giác hệ thống đã kiểm tra dữ liệu thật.

### 4. Tạo Design QA mode

Tạo một cơ chế **Design QA mode** chỉ phục vụ preview trong Figma Make, không đặt nó như tính năng sản phẩm chính.

Có thể dùng một trong các cách đơn giản:

- query parameter `?qa=1`; hoặc
- một nút nhỏ `Design QA` chỉ xuất hiện trong development/preview.

QA mode cho phép designer chọn:

- viewport/state preset;
- role: user, accountant, chief accountant, administrator;
- capability: online, offline, limited capability;
- data scope: known, partially known, unknown;
- component state: default, loading, empty, error, permission denied, stale, conflict, success;
- draft lifecycle: draft, approved, executed, verified — hiển thị riêng biệt;
- evidence state: supplied, inferred, verified, missing, conflict, stale, not applicable.

QA mode phải dùng typed fixtures ở một file riêng, không rải hard-coded data trong từng component. Product UI không được hiển thị control QA khi `qa` không bật.

### 5. Design foundation và component architecture

Refactor presentation layer để giảm inline style lặp lại. Dùng semantic design tokens và reusable component variants.

Tối thiểu cần có:

- `AppShell`
- responsive navigation/sidebar/mobile drawer
- context header
- `Button` variants và sizes
- `Input`, `Textarea`, `Select`
- `StatusBadge`
- `ScopeBadge` hoặc context chip
- `EvidenceCard`
- `EvidenceState`
- `DraftLifecycleBadge`
- `EmptyState`
- `ErrorState`
- `PermissionDeniedState`
- `OfflineState`
- `LoadingSkeleton`
- `Banner/InlineAlert`
- `Drawer/Sheet`
- `Dialog`
- `Tabs/SegmentedFilter` khi thực sự cần
- accessible table/list primitives
- `DiagonalMotif`

Component requirements:

- semantic HTML trước, ARIA chỉ bổ sung khi semantic HTML chưa đủ;
- visible `:focus-visible` không bị inline `outline: none` vô hiệu hóa;
- disabled state có visual + semantic disabled;
- status luôn có icon + label, không dựa vào màu;
- hover, focus, pressed, disabled, loading và error phải khác nhau rõ ràng;
- touch target tối thiểu 44×44px ở mobile;
- không trộn shorthand và longhand CSS gây React style warnings;
- không dùng emoji lẫn lộn như icon system chính; dùng một icon language đơn giản, đồng nhất, restrained;
- giữ border/radius nhỏ và ưu tiên divider/border hơn shadow.

### 6. Responsive shell bắt buộc

Thiết kế và implement thực sự cho bốn breakpoint:

#### 1440–1600px

- Sidebar 264px.
- Context header hiển thị task, company, branch, period, BRAVO version và evidence status.
- Evidence/detail drawer 360–400px.
- Answer column 760–840px khi không bị panel làm hẹp quá mức.

#### 1024px compact desktop

- Sidebar tự collapse về 72px hoặc có compact navigation rõ ràng.
- Context header cho phép wrap có kiểm soát; không cắt task/company/version.
- Evidence drawer chuyển thành toggleable overlay hoặc panel co giãn, không bóp answer column.
- Financial Close Graph phải fit đầy đủ outcome node; không clip node bên phải.

#### 768px tablet

- Không giữ sidebar 264px cố định.
- Navigation chuyển thành drawer.
- Detail/evidence inspector chuyển thành right sheet hoặc full-width secondary view.
- Split view chuyển thành master-detail có back navigation rõ ràng.

#### 390px mobile

- Không có persistent sidebar.
- Dùng compact top app bar với menu, product name và context status.
- Main content dùng toàn bộ chiều rộng.
- Composer không che nội dung, vẫn dùng được khi keyboard xuất hiện.
- Evidence mở thành full-screen sheet có nút đóng và focus management.
- Readiness hiển thị summary + step list; detail mở thành sheet hoặc màn hình kế tiếp.
- Graph mặc định dùng accessible list view; không cố ép sơ đồ desktop vào 390px.
- Approval list/detail xếp dọc; action bar sticky nhưng không che nội dung.
- Không có horizontal clipping hoặc text chỉ còn vài ký tự mỗi dòng.

Ở mọi breakpoint, kiểm tra 200% zoom và nội dung tiếng Việt dài.

### 7. Hoàn thiện từng màn hình

#### A. Sign in

Single job: xác thực và xác định trusted environment.

- Giữ desktop two-column hiện tại vì direction tốt.
- Ở mobile chuyển thành single-column; rút gọn phần thesis nhưng vẫn giữ logo và một `//` moment.
- Tạo các visual state: default, loading, invalid credentials, provider unavailable, offline/local-only, SSO-only, password-enabled, environment unknown.
- SSO và email/password chỉ là prototype interactions; không tuyên bố đã xác thực thật.
- Error phải nói rõ điều gì thất bại và bước tiếp theo.

#### B. Application shell

- Admin navigation chỉ xuất hiện trong admin fixture/role.
- Permission-limited role không nhìn thấy menu, badge count hoặc metadata không được phép.
- Unknown company/branch/period/version phải hiển thị rõ, không tự điền.
- Thêm mobile navigation drawer và compact desktop collapse.
- Share/More phải có disabled/permission states và accessible labels.

#### C. New conversation

- Giữ role-aware greeting, composer và realistic task starters.
- Task starters không chứa claim đã kiểm tra hoặc dữ liệu cụ thể giả.
- Recent conversations phải có empty/loading/error/permission-limited states.
- Attachment có states: idle, uploading, processing, ready, failed, removed.
- Auto profile phải có selector rõ ràng và mô tả ngắn, không làm người dùng hiểu rằng đổi profile có thể đổi quyền.
- Hiển thị draft-only/evidence policy ngắn gọn, không thành legal wall of text.

#### D. Active conversation + Evidence drawer

- Giữ bố cục center conversation + optional evidence drawer ở desktop.
- Không hiển thị chain-of-thought, internal steps hoặc tool mechanics.
- Dùng answer structure tự nhiên: outcome understood → applicable prerequisites → next action → uncertainty → one targeted clarification.
- Citation inline và citation chips phải focus đúng EvidenceCard.
- EvidenceCard phải thể hiện: claim, provenance class, source/locator nếu có, company/period/version scope, approval/effective status, stale/conflict/missing warning.
- Khi evidence chưa có, dùng missing state; không tạo source giả.
- Tạo states: initial, streaming, stopped, complete, no evidence, stale evidence, conflicting evidence, unavailable source, error, cancelled, offline/limited capability.
- Streaming không gây layout jump; có `aria-live` phù hợp nhưng không đọc lại toàn bộ answer mỗi token.
- Mobile evidence drawer là full-screen sheet, giữ được vị trí hội thoại khi đóng.

#### E. Financial Close Readiness

Giữ Evidence Rail và tám prerequisite groups:

1. Phạm vi và kỳ báo cáo
2. Chứng từ nguồn đã ghi nhận
3. Đối chiếu sổ phụ
4. Nghiệp vụ định kỳ áp dụng
5. Bút toán cuối kỳ
6. Kiểm soát đóng kỳ
7. Ánh xạ báo cáo và số dư đầu kỳ
8. Báo cáo và soát xét chênh lệch

Yêu cầu:

- Mỗi node có status, reason, evidence availability, responsible role và next safe action.
- Không dùng readiness percentage, donut hoặc speedometer.
- Default state là unknown/not assessed khi scope hoặc evidence chưa có.
- Tạo đầy đủ: all-not-assessed, partially assessed, missing evidence, conflict, stale, not applicable, permission boundary, loading, empty, error, offline.
- Summary counts chỉ xuất hiện nếu fixture cho phép; permission boundary không được rò hidden count.
- Mobile dùng list/accordion hoặc master-detail sheet; không clip rail.

#### F. Financial Close Evidence Graph

Giữ curated left-to-right dependency map ở desktop. Đây không phải force-directed graph.

Phải bổ sung:

- search;
- filters: milestone, status, evidence type, period, responsible role;
- zoom in/out;
- fit all;
- fit selected;
- reset view;
- clear filters;
- selection inspector;
- accessible hierarchical list/table equivalent;
- keyboard traversal theo dependency order;
- visible focus trên node;
- empty, loading, error, permission boundary và filtered-no-results states.

Rules:

- Desktop graph không clip ở 1024px.
- Mobile mặc định mở list view; graph là tùy chọn nếu đủ không gian.
- Permission boundary dùng neutral masked node; không tiết lộ hidden labels, node counts hoặc edges.
- Không tạo table names, menu names, version facts hoặc verified evidence giả.
- Node selection và citation linking được mô phỏng bằng shared fixture IDs để sau này có thể nối API.

#### G. Draft and Approval Review

- Desktop dùng queue + detail; mobile dùng stacked list → detail.
- Hiển thị rõ: purpose, scope, before/after, evidence status, validation, risk, missing checks, requester, reviewer, timestamp và audit trail.
- Tạo riêng các state: draft, ready for review, validation failed, changes requested, rejected, approved, executed, verified, stale revision, permission denied.
- Không dùng cùng màu/label để làm Approved giống Executed hoặc Verified.
- Khi thiếu validation/evidence quan trọng, thiết kế state “Không thể phê duyệt” với lý do và next action.
- `Yêu cầu chỉnh sửa` mở dialog có textarea bắt buộc trong prototype.
- Approve/Reject là visual simulation và phải hiển thị confirmation; không tuyên bố đã ghi vào BRAVO ERP.

#### H. Knowledge Library

- Desktop ưu tiên governed table/list, không dùng decorative card grid.
- Hiển thị các field ở dạng component-ready: owner, source type, BRAVO version, effective date, approval, visibility, ingestion, traceability, supersession/conflict.
- Khi metadata không có, hiển thị `Chưa xác định`, không tự tạo.
- Tạo list, detail, upload/review, ingesting, ingestion failed, empty, superseded, conflict, permission-limited, offline states.
- Mobile chuyển table thành readable stacked records, không bỏ các governance field quan trọng.

#### I. Administration and Audit

- Đây là role-gated design surface.
- Thiết kế overview cho identity/scope, runtime policy, controlled cloud egress, corpus governance, audit events, failed safety checks và service health.
- Không hiển thị secret, credential, hidden user hoặc tenant metadata.
- Có states: overview, audit detail, degraded, blocked egress, policy conflict, permission denied, mobile read-only.
- Nếu chưa đủ thời gian, vẫn phải hoàn thành design states và navigation structure; không để generic placeholder icon/text như hiện tại.

### 8. Content design

Ngôn ngữ chính là tiếng Việt, direct và professional.

- Action dùng động từ cụ thể: `Lưu thay đổi`, `Yêu cầu bổ sung`, `Mở bằng chứng`, `Quay lại hội thoại`.
- Label, button, toast/confirmation phải dùng cùng một từ.
- Empty state nêu hành động tiếp theo.
- Error state nêu điều gì thất bại và cách khắc phục.
- Không dùng `Hoàn thành` khi thực tế chỉ là `Đã phê duyệt` hoặc `Bản nháp`.
- Không dùng các câu `đã kiểm tra`, `đã thực hiện`, `chính xác`, `đã xác minh` nếu không nằm trong QA fixture được đánh dấu minh họa.
- Không dùng copy marketing trong workspace nghiệp vụ.

### 9. Accessibility acceptance criteria

- WCAG 2.2 AA contrast.
- Keyboard-only sử dụng được mọi screen và dialog.
- Visible focus không bị cắt bởi overflow container.
- Mobile target tối thiểu 44px.
- Drawer/dialog quản lý focus: focus vào title/first action khi mở, trap trong modal, trả focus về trigger khi đóng.
- Semantic headings theo thứ tự.
- Form có label thật; icon-only button có accessible name.
- Status không dựa vào màu.
- Graph có equivalent list/table và logical keyboard order.
- `prefers-reduced-motion` được tôn trọng.
- Conversation usable ở 200% zoom.
- Loading/streaming dùng live-region có kiểm soát.

### 10. Motion

- Chỉ dùng 120–180ms cho hover/panel transition.
- `//` có thể advance một lần khi prerequisite chuyển sang verified trong QA mode.
- Không ambient motion, particle, continuous gradient hoặc decorative animation.
- Skeleton không chạy khi reduced motion bật.

### 11. Trình tự thực hiện bắt buộc

Không sửa tất cả một cách ngẫu nhiên. Thực hiện theo thứ tự:

1. Audit code hiện tại và viết một design implementation plan ngắn.
2. Chuẩn hóa tokens và component primitives.
3. Tạo typed fixture layer + Design QA mode.
4. Implement deterministic local product-state model và các transition/scenario ở mục 2A.
5. Sửa responsive AppShell.
6. Hoàn thiện Sign in và New Conversation.
7. Hoàn thiện Active Conversation + Evidence drawer.
8. Hoàn thiện Financial Close Readiness.
9. Hoàn thiện Financial Close Graph + list equivalent.
10. Hoàn thiện Draft Approval.
11. Hoàn thiện Knowledge Library.
12. Hoàn thiện Administration and Audit.
13. Chạy cross-screen state consistency, responsive, accessibility và content audit toàn app.

Sau mỗi bước, tự review và sửa ngay:

- có còn hard-coded exact claims không;
- có responsive ở 1440/1024/768/390 không;
- có đủ states không;
- có hidden permission data/count không;
- có focus/touch target đúng không;
- có component/style duplication không;
- có làm mất visual quality hiện tại không.

### 12. Deliverables

Khi hoàn thành, project phải có:

1. Design-complete interactive prototype với tất cả màn hình kể trên.
2. Responsive implementation thực sự ở 1440, 1024, 768 và 390px.
3. Centralized typed fixtures, không hard-code dữ liệu trong screen components.
4. Deterministic local product-state model cho TaskBrief, scope, prerequisite, evidence, correction/task switch, draft lifecycle và permission/capability scenarios.
5. Design QA mode để kiểm tra role, capability, product flows và mọi UI state.
6. Accessible graph list/table equivalent.
7. Không còn invented exact financial/schema/version/evidence claims trong product-default view.
8. Không có dead-end button trong prototype: button phải navigate, open/close, toggle state hoặc được disabled có lý do.
9. Một file `PRODUCT-LOGIC.md` mô tả:
   - canonical domain/UI state;
   - transition rules;
   - cross-screen synchronization IDs;
   - draft lifecycle;
   - permission/capability UX contract;
   - mapping của 14 QA scenarios.
10. Một file `DESIGN-QA-RESULTS.md` ghi:
   - screen/state đã hoàn thành;
   - breakpoint đã kiểm tra;
   - accessibility checks đã thực hiện;
   - known design limitations còn lại;
   - xác nhận chưa nối API/backend.

### 13. Final stop gate

Không tuyên bố hoàn thành nếu còn một trong các lỗi sau:

- sidebar 264px vẫn xuất hiện ở 390px;
- main workspace bị clip ở mobile;
- graph mất node ở 1024px;
- không có graph list equivalent;
- admin menu xuất hiện cho non-admin fixture;
- product-default view còn số tiền, tỷ lệ, account, version, locator hoặc verified claim giả;
- missing/loading/error/permission/offline states chỉ tồn tại trong tài liệu nhưng không preview được;
- Approved, Executed và Verified vẫn bị trình bày như cùng một state;
- correction, cancellation, task switch hoặc revision không làm state thay đổi đúng;
- readiness/evidence/graph/draft dùng các fixture state mâu thuẫn nhau;
- approve tự chuyển thành executed/verified;
- scope unknown bị tự động điền hoặc facts từ task epoch cũ bị kế thừa;
- drawer/dialog không usable bằng keyboard;
- touch targets nhỏ hơn 44px ở mobile;
- console còn React style warnings do conflicting CSS properties.

Trước khi chỉnh code, hãy tóm tắt ngắn design implementation plan, product-state model và những phần sẽ giữ nguyên. Sau đó thực hiện toàn bộ vòng chỉnh sửa, tự kiểm tra và cập nhật cả `PRODUCT-LOGIC.md` lẫn `DESIGN-QA-RESULTS.md`.

---

## Prompt bổ sung nếu Figma Make dừng giữa chừng

Nếu phiên đầu không hoàn thành hết, dùng prompt sau để tiếp tục:

```text
Tiếp tục đúng MASTER PROMPT trong plans/09-FIGMA-MAKE-CONTINUATION-PROMPT.md.

Đọc DESIGN-QA-RESULTS.md và source hiện tại, không thiết kế lại các phần đã pass. Chọn gate chưa pass có severity cao nhất theo thứ tự:
1) invented exact claims;
2) mobile/compact responsive clipping;
3) permission leakage;
4) missing component states;
5) accessibility/focus/touch targets;
6) consistency/refactor.

Hoàn thành gate đó trên tất cả screen liên quan, kiểm tra 1440/1024/768/390, cập nhật DESIGN-QA-RESULTS.md bằng bằng chứng cụ thể rồi mới chuyển gate tiếp theo. Chưa nối API/backend và không tạo backend mock.
```
