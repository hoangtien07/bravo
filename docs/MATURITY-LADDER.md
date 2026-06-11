# MATURITY-LADDER — bản đồ leo bậc L1→L4 cho bravo

> Bối cảnh ([phân tích product-version]): bravo là sản phẩm **DỌC** (như agent-ai/Logistics AI OS), benchmark theo agent-ai — KHÔNG theo letta/docsgpt (ngang). bravo đang **L1**, thấp hơn mọi tham chiếu 1–2 bậc.
> **Kỷ luật xuyên suốt (chống đào-sâu-engine):** ❌ KHÔNG thêm tính năng agentic/engine mới cho tới khi **L2 (product surface chạy online) XONG + ≥1 user thật**. Mỗi bậc có **cổng validate** — không lên bậc sau khi chưa qua cổng.

---

## L1 — Engine + unit test ✅ (ĐANG Ở ĐÂY)
- **Định nghĩa:** lõi chạy, unit-test xanh, governance primitives đúng.
- **Trạng thái:** 8 WP committed; ~100 test xanh; RLS/verify/maker-checker verify trên Postgres thật.
- **Cổng (đã qua):** suite xanh + DB smoke.
- **⚠ Bẫy L1:** *ở lại đây xây thêm engine* (loop tinh vi hơn, eval phức tạp hơn). Đây là cái bravo đang có nguy cơ mắc. **Dừng thêm engine.**

## L1 → L2 — Demo chạy E2E + có hình hài SẢN PHẨM
- **Cần:**
  1. **Deploy online** — [DEPLOY-DEMO.md](DEPLOY-DEMO.md) (GCP+Caddy).
  2. **Product surface** — [PRODUCT-SURFACE.md](PRODUCT-SURFACE.md) (shell + answer-card drill-down + draft review + sources).
  3. **Bật thư viện proven** — [FIX-REUSE-PLAN.md](FIX-REUSE-PLAN.md) R1–R3 (Docling + bge-m3 local; tự xảy ra khi build image) → corpus thật nạp được (gồm `.docx` + bảng).
  4. **E2E cloud thật + đo cơ bản** — chạy được trên LLM cloud thật; đo agentic-vs-RAG ([AGENTIC-SPIKE-WS0 §5]).
- **Cổng validate (định nghĩa "L2"):** **một người lạ đăng nhập online tự hoàn thành** 5 kịch bản smoke ([DEPLOY-DEMO §5]) — hỏi tri thức có nguồn · hỏi số thấy drill-down+RLS+verify · duyệt nháp · xem nguồn — **không cần bạn lái**.
- **Metric:** demo hoàn thành 5/5 kịch bản ổn định; citation hiện đúng nguồn; 0 rò RLS trong demo; Δ(agentic vs RAG) đo được.
- **⚠ Bẫy L2:** thêm tính năng mới thay vì **đánh bóng surface + làm cho nó đáng tin**.

## L2 → L3 — Pilot DATA THẬT + USER THẬT (bậc quyết định giá trị)
- **Cần:**
  - **Data thật:** hoặc (a) **ERP read-only API** + catalog metric kế toán duyệt (mở Demo-B số thật), hoặc (b) **corpus tài liệu thật của 1 phòng ban** (mở Demo-A giá trị thật ngay cả khi ERP chưa có).
  - **User thật:** helpdesk/kế toán BRAVO dùng cho câu hỏi THẬT, đều đặn.
  - **Chuyển ngữ nghĩa metric** sang thật (gross/net, VAT, kỳ khoá sổ — kế toán xác nhận).
- **Cổng validate (định nghĩa "L3"):** **≥1 phòng ban dùng hàng tuần cho việc thật và báo có giá trị**; citation accuracy ≥95% trên corpus thật; **0 rò RLS** trong dùng thật; kế toán xác nhận "tin số".
- **Metric:** % câu helpdesk tự phục vụ (mục tiêu 30–40%); giảm giờ/ticket; số câu số-liệu tự phục vụ/tuần; % nháp duyệt-không-sửa.
- **⚠ Bẫy L3:** mở rộng phạm vi (thêm phòng ban/tính năng) **trước khi** một pilot chứng minh giá trị. *(Đây đúng cái nghiên cứu cảnh báo: 50% pilot chết vì "giá trị không rõ".)*

## L3 → L4 — Đóng gói & thu tiền (on-prem add-on)
- **Cần:**
  - **Installer on-prem** (Helm/air-gapped) — đội triển khai BRAVO cài tại site khách trong vài giờ.
  - **Qwen LOCAL thật** — [FIX-REUSE-PLAN R5](FIX-REUSE-PLAN.md) (Ollama/vLLM) → **moat chủ quyền hết ảo** + pass^k đo được.
  - **Air-gapped artifact** (bake model offline) + security/compliance sign-off (PDPD/Luật 91-2025).
  - **Định giá per-site/module** + demo "đinh" + tài liệu bán.
- **Cổng validate (định nghĩa "L4"):** **một khách hàng cam kết/trả tiền deploy on-prem và gia hạn.**
- **Metric:** số site ký; retention; biên lợi nhuận add-on.
- **⚠ Bẫy L4:** xây tính năng khách **không yêu cầu**; bán bằng "rẻ" thay vì "chủ quyền + không bịa số" (ADR-0006).

---

## Bản đồ tài liệu → bậc
| Tài liệu | Phục vụ bậc |
|---|---|
| 8 WP + tests | L1 (xong) |
| [DEPLOY-DEMO.md](DEPLOY-DEMO.md) · [PRODUCT-SURFACE.md](PRODUCT-SURFACE.md) · [FIX-REUSE-PLAN.md](FIX-REUSE-PLAN.md) R1–R3 | **L1→L2** |
| ERP-INTEGRATION-REQUEST · METRIC-CATALOG (kế toán duyệt) · pilot | L2→L3 |
| FIX-REUSE R5 (Qwen local) · Helm/air-gapped · ADR-0006 pricing | L3→L4 |

## Một câu để dán lên tường
> **Mỗi bậc = một thứ được CHỨNG MINH trên điều kiện thật, không phải thêm một thứ được XÂY.** bravo thắng khi leo bậc (deploy → pilot → bán), KHÔNG khi đào sâu engine. agent-ai ở L3–4 vì nó **chứng minh** với user thật; bravo lên L2 trước — rồi một pilot thật, không phải mười tính năng nữa.
