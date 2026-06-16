# PRODUCT-SURFACE — "Finance AI OS" (mượn shell agent-ai để leo L1→L2)

> Mục tiêu: biến bravo từ "1 ô textbox" thành **một product surface** kiểu agent-ai (Logistics AI OS) — **làm governance HIỂN THỊ** (drill-down số→nguồn, badge RLS, verify-status, draft review). Đây là **việc FRONTEND + API mỏng, KHÔNG thêm engine** (kỷ luật L1→L2).
> Nền đã có (tận dụng, không viết lại): `frontend/index.html`+`app.js` (login + ask + agentic toggle + badge grounded/cloud + citations có cấu trúc); API `/api/auth/login` `/api/me` `/api/ask` `/api/agent/ask` `/api/sources` `/api/drafts`. Giữ **static, no-build** (vanilla JS) cho demo.
> Đối chiếu agent-ai (ảnh 1): domain-nav · live agent stream · artifact Review/Download · workspace files. Map sang tài chính dưới đây.

## Nguyên tắc (chống đào-sâu-engine)
- Mỗi PS chỉ chạm `frontend/` + (nếu cần) **API mỏng** trả thêm dữ liệu engine ĐÃ có (provenance/verdict). **KHÔNG** thêm tool/loop/metric mới.
- Mọi số liệu phải **truy được nguồn trên UI** — đó là điểm khác biệt DUY NHẤT cần xây (tương đương memory-graph của Letta).

---

## PS-1 — Shell + domain nav (thay "1 card" bằng "sản phẩm")
**Việc:** dựng layout shell: sidebar/top-nav 4 mục — **Hỏi-đáp** · **Số liệu** (hỏi tài chính) · **Nháp chờ duyệt** · **Nguồn tài liệu**. Header hiện user + phòng ban + nút đăng xuất. Agent **nhúng trong** mục, không tách rời.
**Backend:** đã đủ (`/api/me`). **Acceptance:** đăng nhập → thấy shell có 4 mục điều hướng được; mục đang chọn highlight; mobile co lại gọn.

## PS-2 — Answer card có DRILL-DOWN số→nguồn + badge RLS + verify (★ điểm khác biệt)
**Việc (frontend):** render câu trả lời thành **thẻ** gồm:
- Đoạn trả lời.
- **Bảng "Số liệu & nguồn"**: mỗi số engine trả về → `giá trị (đơn vị/scale)` + **nút "Nguồn"** mở `provenance` (metric-id+kỳ, hoặc tài liệu+trang/ô). *(Đây là drill-down — làm zero-hallucination HIỂN THỊ.)*
- **Badge verify-gate:** `✓ Mọi số có nguồn` / `⚠ Đã ẩn số chưa kiểm chứng` / `⛔ Từ chối — thiếu căn cứ`.
- **Badge RLS:** `Bạn thấy theo quyền: <phòng ban>`; nếu có ngoài-quyền → hiện *hint* loại+số-lượng (KHÔNG tiêu đề — `out_of_scope_hint` đã có).
- **Badge egress:** `🔒 local` / `☁ cloud (đã audit)` (đã có).
- Nhãn **"⚠ Cần kế toán xác nhận"** cho mọi thẻ có số tài chính.
**API mỏng cần thêm (KHÔNG engine):** `routes_agent` trả thêm `engine_values: [{metric_id, value, scale, unit, provenance, is_demo}]` + `masked: [..]` (lấy từ `MetricResult` + `VerifyVerdict` loop ĐÃ tạo — chỉ serialize ra). RLS scope từ `/api/me`.
**Acceptance:** hỏi *"Doanh thu thuần Q2?"* → thẻ hiện số **52,8 tỷ** + nút Nguồn mở `mock:doanh_thu_thuan ky=2026-Q2`; badge `✓ có nguồn` + `Bạn thấy theo quyền: Kế toán` + nhãn cần-xác-nhận. LLM bịa "9999 tỷ" → badge `⚠ đã ẩn` + số bị mask.

## PS-3 — Draft review (mượn "Review/Download" của agent-ai → maker-checker hiển thị)
**Việc (frontend):** mục **Nháp chờ duyệt**: list `/api/drafts` (chỉ pending trong quyền — RLS đã lọc); mỗi nháp = thẻ {kind, payload đẹp, người tạo, thời gian} + nút **Duyệt** / **Từ chối**. Hiện rõ khi **không được tự duyệt** (`created_by==bạn` → nút Duyệt mờ + tooltip "maker-checker: không tự duyệt").
**Backend:** đã đủ (`/api/drafts` GET/approve/reject; anti-self-approval trả 403). **Acceptance:** tạo nháp bằng `ketoan` → `nhansu`/khác phòng KHÔNG thấy; người tạo bấm Duyệt → 403 hiện "không tự duyệt"; người khác duyệt → trạng thái `approved`.

## PS-4 — Panel Nguồn tài liệu (mượn "workspace files" của agent-ai)
**Việc (frontend):** mục **Nguồn**: list `/api/sources` (RLS-filtered) với **badge scope** (global / phòng ban) + trạng thái ingest; nút **Upload** (gọi `/api/sources` POST, chọn phòng ban scope). **Acceptance:** thấy 19 chương + tài liệu đã nạp; upload 1 file scoped phòng Kế toán → chỉ `ketoan`/admin thấy.

## PS-5 — Agent step-stream (mượn "Live agent stream" — nice-to-have, để cuối)
**Việc:** hiện các bước loop (retrieve → tool-call → verify → answer) dạng timeline khi chạy agentic. Cách rẻ: `routes_agent` trả `steps: [{type, tool?, summary}]` (loop ĐÃ có observations) → frontend render list; (nâng cao sau: SSE stream thật). **Acceptance:** câu 2-bước hiện 2 dòng tool-call + 1 dòng verify trước câu trả lời. *(Có thể HOÃN qua L2.5 — không chặn demo.)*

---

## Thứ tự & cổng ra L1→L2
1. **PS-1** (shell) → **PS-2** (answer-card drill-down — quan trọng nhất) → **PS-3** (draft review) → **PS-4** (sources). **PS-5 hoãn.**
2. **Cổng "có hình hài sản phẩm":** một người lạ đăng nhập online (sau [DEPLOY-DEMO](DEPLOY-DEMO.md)) tự làm được: hỏi tri thức (thấy nguồn) · hỏi số (thấy drill-down + RLS + verify) · xem & duyệt nháp · xem nguồn — **không cần bạn lái**.
3. **Đo (L2):** 5 kịch bản smoke ([DEPLOY-DEMO §5]) chạy ổn; **agentic-vs-RAG** đo được ([AGENTIC-SPIKE-WS0 §5]) — nếu agent loop không hơn RAG đơn-shot ≥ ngưỡng cho tri thức → để RAG đơn-shot cho Hỏi-đáp, agent loop chỉ cho mục Số liệu.

## Ranh giới (đừng làm)
KHÔNG SPA nặng/build-step (giữ vanilla cho demo) · KHÔNG thêm tool/metric/loop mới · KHÔNG memory-graph kiểu Letta (over-scope) · KHÔNG agent tự-cấu-hình phơi cho user (Letta đã chứng minh sai surface — cấu hình ở code/playbook).
