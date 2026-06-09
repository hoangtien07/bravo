# 0008. arkon là chỉ-học-pattern, viết lại — KHÔNG tái dùng code

- **Trạng thái:** Accepted (quyết định: viết lại)
- **Ngày:** 2026-06-09
- **Người quyết định:** BRAVO
- **Liên quan:** [ADR-0007](0007-code-strategy.md), [reference/arkon-notes.md](../reference/arkon-notes.md).

## Bối cảnh (Context)
arkon mang giấy phép **PolyForm Internal Use License 1.0.0** — chỉ cho dùng nội bộ, **cấm** đưa code vào sản phẩm phân phối/bán. BRAVO AI Copilot dự kiến bán add-on. Câu hỏi: xác nhận quyền sở hữu để (có thể) chuyển thể trực tiếp code arkon, hay viết lại từ pattern?

## Quyết định (Decision)
**BRAVO chọn VIẾT LẠI.** arkon được dùng **chỉ làm tài liệu tham khảo — học pattern, viết lại từ đầu** (RLS tầng SQL, MCP scoped, draft workflow, MRP). **KHÔNG copy/chuyển thể code arkon** vào codebase sản phẩm, *bất kể* quyền sở hữu.

Hệ quả: **không cần** theo đuổi xác nhận sở hữu/relicense arkon. Rủi ro giấy phép PolyForm được **loại bỏ hoàn toàn**. Điều này xác nhận đường mặc định của [ADR-0007] (arkon = pattern-only).

## Hệ quả (Consequences)
- Tích cực: **không vướng pháp lý**; kiến trúc sạch, tự chủ; viết lại cho phép áp 4 nguyên tắc bất biến + RLS tập trung ngay từ thiết kế, không gánh giả định của arkon.
- Tiêu cực/nợ: chậm hơn so với chuyển thể code có sẵn — phải tự code lại RLS engine, MCP, draft workflow, MRP. Bù lại: code chỉ đọc arkon làm "spec sống" để tham chiếu khi viết.
- docsgpt (MIT) & letta (Apache 2.0) **vẫn được chuyển thể code** (không đổi) — chỉ arkon là pattern-only.

## Tham chiếu
PolyForm Internal Use 1.0.0. [ADR-0007](0007-code-strategy.md) bản đồ "lấy gì từ đâu".
