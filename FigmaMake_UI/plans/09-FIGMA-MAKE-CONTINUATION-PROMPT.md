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