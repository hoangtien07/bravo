# 0031. Pilot đóng cổng L2→L3 = U2 (Copilot AP) đơn lẻ; U1 (hỏi-đáp tri thức) là tiện ích nền

- **Trạng thái:** **Superseded before acceptance** (2026-07-31) bởi
  [ADR-0032](0032-first-v2-demonstrator-reconciliation-exception.md). Tài liệu này được giữ làm
  evidence lịch sử; nó không còn chọn demonstrator hoặc pilot hiện tại.
- **Ngày:** 2026-07-20
- **Người đề xuất:** Rà soát use-case (inventory grounded từ code, branch `feat/v2-p0-containment`) + Hội đồng cố vấn 5 thành viên.
- **Căn cứ:** Council review 2026-07-20 (5/5 phản hồi, tổng hợp trong ADR này). Xây trên [ADR-0016](0016-pivot-standalone-ap-vertical.md) (mũi nhọn AP, Accepted), [MATURITY-LADDER.md](../MATURITY-LADDER.md) (định nghĩa cổng L2/L3), [ADR-0030](0030-offline-as-dated-exit-criterion.md) (offline là exit-criterion), quyết định pilot V2 cloud-only (memory 2026-07-19). KHÔNG sửa 4 bất biến.

## Bối cảnh (Context)

Câu hỏi cần chốt: **use case nào làm pilot ĐẦU TIÊN để đóng cổng L2→L3** (chứng minh giá trị với ≥1 user thật), khi lõi đã build xong và kỷ luật là "dừng thêm engine".

Inventory use-case grounded từ code cho thấy **chỉ 2 use case chạy E2E trên DATA THẬT**:

| | U1 — Hỏi-đáp tri thức | U2 — Copilot AP |
|---|---|---|
| Phân loại | **RAG thuần** (không phải bài toán agent) | **Agent-write** (tool tất định + maker-checker) |
| Data | Corpus tri thức hỗn hợp ~72 nguồn thật (user_guide+kqpt_ptnv+technical_manual, xem [USECASE-INVENTORY.md](../USECASE-INVENTORY.md)) | Hoá đơn upload thật + DB thật |
| Giá trị/willingness-to-pay | Trung bình (ChatGPT Enterprise làm được) | Cao (moat 4 bất biến; mũi nhọn bán add-on) |
| Tần suất | Cao | Thấp hơn (theo đợt hoá đơn) |

Ba use case còn lại (U3 hỏi-đáp số liệu, U4 anomaly, U5 tax) chạy **MOCK** (`BravoErpDataSource` chưa hiện thực) → bất khả thi ngay, loại khỏi pilot.

## Quyết định (Decision)

> **Pilot đóng cổng = U2 (Copilot AP), ĐƠN LẺ, trên PHẠM VI CHỨNG TỪ HẸP + luồng tất định.**
> **U1 = tiện ích nền opt-in cho cùng nhóm user, KHÔNG gánh KPI cổng, chỉ bật SAU khi vá blocker chí mạng.**

Chi tiết thực thi: [PILOT-U2-SCOPE.md](../PILOT-U2-SCOPE.md).

### Vì sao U2 trước, không chạy song song ngang hàng
- **Product:** cổng L3 hỏi "có giá trị ai trả tiền không" — U2 trả lời được, U1 thì không ở mức thuyết phục ngân sách. Chạy cả hai làm giá trị *mờ* hơn (đúng "bẫy L3", [MATURITY-LADDER.md:31](../MATURITY-LADDER.md#L31)).
- **Security:** luồng lõi U2 **tất định, KHÔNG gọi LLM** → dữ liệu nhạy (MST/NCC/số tiền) **không rời mạng** ra cloud, kể cả dưới `cloud_only`. U1 bắt buộc egress toàn văn chunk.
- **RAG:** U2 có maker-checker (người duyệt trước khi xuất) chặn ảo tưởng *trước khi ra ngoài*; U1 trả thẳng cho user.

### Nghịch lý cốt lõi
Dưới cấu hình `cloud_only` hiện tại, **luồng tất định của U2 an toàn hơn luồng RAG của U1**: [router.py:84](../../app/llm/router.py#L84) return `cloud` TRƯỚC mọi kiểm tra độ nhạy → cơ chế ghim-local bị vô hiệu; tài liệu nạp nhầm (HR/lương) sẽ egress không phanh.

## Phán quyết Hội đồng (2026-07-20)

| Thành viên | Phán quyết | Cốt lõi |
|---|---|---|
| product-strategist | ✅ GO | U2 pilot chính; U1 nền không KPI |
| security-rls-auditor | ⚠️ GO-WITH-CHANGES | U2 trước; U1 NO-GO tới khi vá C1 (cloud_only bypass) + H1 (audit actor_id) |
| erp-accounting-expert | ⚠️ GO-WITH-CHANGES | U2 phải thu hẹp phạm vi; 3 bug định khoản chí mạng |
| rag-architect | ⚠️ Có khoảng trống | Nghiêng U2; U1 còn 3 lỗ citation/number-gate |
| onprem-deployment | ⚠️ Có ràng buộc | Chưa drill restore + uploads chưa bền → chặn cả hai |

**Đồng thuận:** U2 là vertical dẫn giá trị. **Bất đồng:** accounting/deployment ban đầu nghiêng U1-first (an toàn số / chín vận hành) — nhưng lý lẽ đó dựa trên giả định "U1 rủi ro ~0" và "corpus không nhạy", mà security + RAG chứng minh **chưa được cưỡng chế trong code**. Khi buộc cưỡng chế, U2 (rủi ro bị con người chặn) nổi lên là pilot an toàn hơn.

## Blocker CHÍ MẠNG (quyền phủ quyết — phải xong TRƯỚC user thật)

**U2 (accounting + security):**
1. 🔴 Chặn cứng ngoại tệ (`currency != VND` → HITL). — ✅ **Đã làm** ([journal.py](../../app/accounting/journal.py) `build_journal_entry`, test `test_foreign_currency_hard_blocked`).
2. 🔴 Cờ phương thức thanh toán cho MỌI hoá đơn (331 mua chịu vs 111/112 trả ngay).
3. 🔴 Giới hạn DN khấu trừ + chi phí SXKD (engine luôn giả định VAT khấu trừ Nợ 1331).
4. 🔴 Khoá đường egress agent/guarded trong pilot — chỉ endpoint tất định [routes_invoices.py:20](../../app/api/routes_invoices.py#L20).
5. 🟠 Nối `crosswalk.is_removed()` vào gate (chặn TK TT200 đã bỏ từ 1/1/2026).

**U1 (nếu bật, kể cả làm nền):**
6. 🔴 SEC-C1: allowlist corpus + assertion pre-egress kể cả dưới `cloud_only`. ⚠ Corpus là hỗn hợp 3 loại (user_guide + technical_manual + kqpt_ptnv 41%) — quyết định rõ `source_type` nào được egress; kqpt/technical nhạy hơn user-guide ([USECASE-INVENTORY.md §3](../USECASE-INVENTORY.md)).
7. 🔴 RAG-C3: number-integrity gate trên `/api/ask`. — ✅ **Đã làm** ([grounded_answer.py](../../app/rag/grounded_answer.py) `answer_grounded`, test `test_ask_number_gate.py`).
8. 🔴 RAG-C1: trang trích dẫn = trang chứa câu trả lời (không phải đầu section).
9. 🟠 SEC-H1 (actor_id trong audit egress) + RAG-C2 (kiểm chứng câu↔citation).

**Cross-cutting (deployment):**
10. 🔴 Chạy restore drill (RTO đang "chưa chạy") + backup off-VM (GCS) + uploads durability.
11. 🟠 Dùng bge-m3 local 1024-dim NGAY cho embedding (tránh nợ re-ingest + giữ text không rời máy).
12. 🟠 Cost cap per-user + ADR scope `cloud_only` với exit-criterion về hybrid ([ADR-0030](0030-offline-as-dated-exit-criterion.md)).

## Phương án đã cân nhắc (Alternatives)

| Phương án | Vì sao loại / chọn |
|---|---|
| **A. U1 làm pilot chính** | ❌ Loại: không chứng minh willingness-to-pay ở mức khác biệt; và dưới `cloud_only` U1 còn rủi ro egress/citation chưa cưỡng chế. |
| **B. Chạy U1 + U2 song song ngang hàng** | ❌ Loại: chia đôi nguồn lực, làm giá trị mờ, đúng bẫy L3; nhân đôi bề mặt rủi ro vận hành. |
| **C. U2 pilot chính + U1 tiện ích nền (không KPI)** | ✅ Chọn: một mũi nhọn giá trị đo được; U1 tái dùng corpus (~0 chi phí) tạo thói quen dùng hằng ngày. |

## Hệ quả (Consequences)

**Tích cực:** một câu chuyện giá trị đo được để bảo vệ ngân sách add-on; rủi ro egress/ảo tưởng thấp nhất; giữ trọn 4 bất biến; không thêm engine mới.

**Tiêu cực / chi phí:** U2 tần suất thấp → dựa U1 nền để giữ engagement; cần hoàn thành các blocker định khoản (#2,#3,#5) trước khi mở cho kế toán thật; U1 chỉ bật sau khi vá C1/C1-citation.

**Tiêu chí đóng cổng (định nghĩa "pilot U2 thành công"):** xem [PILOT-U2-SCOPE.md](../PILOT-U2-SCOPE.md) §Tiêu chí cổng — 2–4 kế toán thật, 4 tuần, ≥100–150 hoá đơn thật; STP ≥70–85%, 0 lệch Nợ=Có lọt gate, 0 rò RLS, giảm ≥40% thời gian/hoá đơn, retention, willingness-to-pay định tính. FAIL ngay nếu có 1 số sai lọt gate hoặc 1 rò RLS.
