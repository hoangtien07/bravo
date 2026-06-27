# 0016. Mũi nhọn đầu tiên = "Copilot AP" ĐỘC LẬP (ship trên chứng từ upload, không phụ thuộc ERP API)

- **Trạng thái:** **Proposed** — chờ chủ dự án duyệt + `/council-review`. CHƯA Accepted, chưa được phép coi là quyết định cuối.
- **Ngày:** 2026-06-26
- **Người đề xuất:** Rà soát phản biện (đối chiếu code thật + 5 repo tham chiếu trong workspace, đặc biệt **agent-ai/Atlas Builder**).
- **Liên quan:** tinh chỉnh thứ tự thực thi của [VISION.md](../VISION.md) & [MATURITY-LADDER.md](../MATURITY-LADDER.md); gỡ phụ thuộc cứng vào [ERP-INTEGRATION-REQUEST.md](../ERP-INTEGRATION-REQUEST.md); KHÔNG sửa 4 bất biến ([ADR-0003](0003-hybrid-llm-strategy.md)/[0004](0004-llm-never-computes-numbers.md)/[0005](0005-no-free-form-sql.md)); xây trên [0010](0010-agent-loop-architecture.md)/[0012](0012-verify-gate-number-integrity.md)/[0014](0014-journal-entry-validator.md). Đối chiếu pattern: [reference/agent-ai-notes.md](../reference/agent-ai-notes.md).

## Bối cảnh (Context)

Rà soát ngày 2026-06 (đối chiếu **tuyên bố ↔ code thật ↔ 5 repo workspace**) phát hiện ba rủi ro hội tụ về cùng một nguyên nhân — **dự án đặt cược cửa ngõ giá trị vào một phụ thuộc ngoài tầm kiểm soát**:

1. **Vòng giá trị đứt ở hai đầu.** Parser hoá đơn + builder bút toán + verify-gate + draft-queue **có thật, có test**. Nhưng đầu vào là **YAML mock** ([mock_source.py](../../app/data_layer/mock_source.py) `is_demo=True`); **ERP client là stub** ([erp/client.py](../../app/erp/client.py) — chỉ TODO, không có httpx); **duyệt nháp không đẩy đi đâu** ([draft_queue.py:107](../../app/erp/draft_queue.py#L107) TODO Phase 3). ⇒ Không chạy được trên dữ liệu thật.

2. **Blocker nằm ngoài đội.** Toàn bộ Phase 2+ chờ **BRAVO ERP (.NET) mở REST API read-only + danh mục view duyệt + hàng đợi staging**. [VISION §8](../VISION.md): *"cập nhật 2026-06: chưa có API read-only — đang xin."* Đã treo nhiều tháng; đội ERP có ưu tiên riêng. Không có deadline cứng và **không có đường vòng**.

3. **Phình bề rộng khi 0 người dùng.** Đã thiết kế 5 hướng agent (anomaly/AR/tax/money-engine/IFRS) + chat + RAG, đúng "bẫy L1" mà [MATURITY-LADDER.md](../MATURITY-LADDER.md) tự cảnh báo. willingness-to-pay 100% giả định.

**Bằng chứng đối chiếu (quan trọng):** repo `../agent-ai` (**Atlas Builder**) là một **hệ agentic VN ĐÃ CÓ NGƯỜI DÙNG THẬT** trong miền tương tự (số liệu, rủi ro pháp lý). Nó ship giá trị **không cần tích hợp ghi vào hệ nguồn**: nhận **chứng từ → pipeline tất định → cổng audit (cảnh báo) → cổng handover (chặn, exit-code) → bàn giao artifact**. Tức: con đường đã được kiểm chứng để ra giá trị sớm ở VN là **ship trên chứng từ + maker-checker**, **không** chờ mở API hệ nguồn.

## Quyết định (Decision — ĐỀ XUẤT)

**Chuyển mũi nhọn ship đầu tiên thành "Copilot AP" ĐỘC LẬP**, hoàn chỉnh end-to-end **mà không cần ERP API**:

```
Upload hoá đơn (XML/PDF)  →  Parse (deterministic, đã có)  →  Định khoản nháp
  (rule-first + TT45 ngưỡng TSCĐ + TT219 điều kiện khấu trừ VAT — đã sửa, có test)
  →  Number-Integrity Gate (cân Nợ=Có + truy nguồn số — đã có)
  →  Maker-checker duyệt (đã có draft_queue)
  →  XUẤT artifact bút toán (Excel/CSV/XML) để kế toán NHẬP TAY vào ERP
```

**Nguyên tắc chốt của đề xuất:**
- **Đầu ra = file xuất, KHÔNG ghi ERP.** Thay "đẩy nháp → ERP staging" (cần endpoint ghi của .NET) bằng **xuất file để người nhập tay**. Điều này **còn non-invasive hơn** (con người là cổng ghi cuối) và **bỏ hẳn phụ thuộc API**.
- **ERP API trở thành nâng cấp TÙY CHỌN của Phase sau, không phải cổng gating.** Khi .NET sẵn sàng thì nối thẳng (đầu vào đọc tự động, đầu ra staging) — kiến trúc giữ nguyên.
- **Điều kiện tiên quyết (đã làm trong cùng đợt rà soát):** sửa lỗi định khoản TSCĐ/VAT + đổi tên rõ "Number-Integrity Gate ≠ định khoản đúng" ([account_mapper.py](../../app/accounting/account_mapper.py), [journal.py](../../app/accounting/journal.py), [tests/test_accounting_rules.py](../../tests/test_accounting_rules.py)). Không demo khi rule còn sai.
- **Các agent #2–#4 GIỮ ĐÓNG BĂNG 🧊** cho tới L3 + ≥1 khách thật.

## Phương án đã cân nhắc (Alternatives)

| Phương án | Vì sao loại / chọn |
|---|---|
| **A. Giữ nguyên: chờ ERP API rồi mới ship** (status quo) | ❌ Loại: thời hạn vô định, blocker ngoài tầm; tiếp tục demo trên mock → không có khách, không có dữ liệu giá-sẵn-lòng-trả. |
| **B. Xây tiếp 5 agent trên mock cho "đủ bộ"** | ❌ Loại: phình scope, 0 user validate, vi phạm chính MATURITY-LADDER; rủi ro xây sai cái thị trường không cần. |
| **C. Copilot AP độc lập, ship trên chứng từ upload + xuất file** (đề xuất) | ✅ Chọn: ship được trong tuần (không chờ .NET); tạo user thật → đo willingness-to-pay; dogfood với kế toán/helpdesk BRAVO; giữ trọn 4 bất biến; học đúng pattern agent-ai. |

## Hệ quả (Consequences)

**Tích cực:**
- **Ship không bị chặn** bởi đội .NET; rút ngắn đường tới người dùng thật và dữ liệu willingness-to-pay.
- **Giảm rủi ro #1, #2, #3** cùng lúc (phụ thuộc ngoài, vòng đứt, scope creep).
- Giữ nguyên 4 bất biến: RLS theo phạm vi người upload; non-invasive (xuất file, người nhập); zero-hallucination (rule-first + verify-gate + điều kiện TT45/TT219); offline (parse cục bộ; LLM local tùy chọn).
- Tái dùng ~90% lõi đã có; chỉ cần **giao diện upload + export bút toán + đóng vòng duyệt→xuất**.

**Tiêu cực / chi phí:**
- Tạm **mất điểm "wow" tích hợp ERP sâu**; nhập tay artifact là thủ công (chấp nhận cho MVP, đúng tinh thần maker-checker).
- Cần thêm **format export** (Excel/CSV/XML nhập ERP) + cột truy nguồn (source_ref) — việc nhỏ, có sẵn `source_ref` trong [JournalLine](../../app/accounting/journal.py).
- **draft_queue Phase 3** (push ERP) hoãn lại sau, không bỏ.

**Điều kiện để chuyển Proposed → Accepted:**
1. Chủ dự án xác nhận đổi định vị mũi nhọn (Finance "AI OS" → "Copilot AP độc lập trên TT99").
2. `/council-review` thông qua (đặc biệt lăng kính kế toán + chiến lược + RLS cho luồng upload).
3. Có ≥3 cuộc phỏng vấn kế toán/CFO BRAVO xác nhận pain-point AP đáng trả tiền (song song, không chặn code).

> Nếu KHÔNG Accepted: tài liệu này vẫn có giá trị ghi lại rủi ro phụ thuộc ERP API + lựa chọn đã cân nhắc, để xem lại khi tình huống .NET thay đổi.
