# 0002. Kiến trúc = tổng hợp pattern từ arkon + docsgpt + letta (mượn, không fork)

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-08
- **Người quyết định:** Đội dự án BRAVO AI Copilot
- **Liên quan:** [VISION.md §1](../VISION.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [reference/](../reference/)

## Bối cảnh (Context)
BRAVO AI Copilot cần đồng thời: (a) RLS phòng ban + workflow duyệt, (b) nạp đa định dạng + bóc bảng + RAG offline, (c) agent có bộ nhớ + tool-calling gọi ERP. Có sẵn ba mã nguồn trong workspace, mỗi cái giải quyết xuất sắc *một* phần: **arkon** (a), **docsgpt** (b), **letta** (c). Câu hỏi: xây từ đầu? fork một repo rồi mở rộng? hay tổng hợp? Quyết định này định hình toàn bộ kiến trúc nên cần chốt sớm và rõ.

## Các phương án đã cân nhắc (Options)
1. **Xây mới hoàn toàn.** Ưu: sạch, vừa khít. Nhược: tốn công khổng lồ, lặp lại sai lầm người khác đã giải (nhất là RLS tầng SQL và parse bảng — rất khó làm đúng).
2. **Fork một repo làm nền (vd arkon) rồi nhồi phần còn lại.** Ưu: có ngay bộ xương an ninh. Nhược: kéo theo nợ kỹ thuật & giả định của repo gốc; trộn ingestion docsgpt + agent letta vào một codebase lạ rất rối; khó tách bạch cái BRAVO sở hữu.
3. **Tổng hợp có chủ đích — mượn *pattern*, không fork nguyên khối.** Lấy mô hình RLS của arkon, pipeline ingestion của docsgpt, mô hình memory+tool của letta; hợp nhất dưới *một* kiến trúc BRAVO mới với bảo mật là mặc định; ba repo giữ vai trò **tài liệu tham chiếu chỉ-đọc**.

## Quyết định (Decision)
Chọn **Phương án 3**. Kiến trúc BRAVO AI Copilot là sự **tổng hợp pattern**:
- **An ninh/RLS/duyệt** ⟵ arkon (filter trong SQL; MCP scoped token; workflow nháp→duyệt; Verify chống ảo tưởng).
- **Ingestion/RAG/offline** ⟵ docsgpt (Docling + bảng; abstraction LLM/vector; đường offline) — **mở rộng** provenance số trang/ô và **thêm** RLS (docsgpt không có).
- **Agent/memory/tool/approval** ⟵ letta (3 tầng nhớ; tool sandbox; `requires_approval`) — lõi gọn, mọi tool đi qua RLS.
- **Tích hợp ERP** ⟵ BRAVO tự xây (read-only REST/view đã duyệt; Draft Queue về giao diện ERP).

Ba repo là **chỉ-đọc** (đã chặn Write/Edit trong `.claude/settings.json`).

## Hệ quả (Consequences)
- Tích cực: tận dụng giải pháp đã chứng minh cho các bài toán khó (RLS, parse bảng, memory); BRAVO **sở hữu** kiến trúc hợp nhất, không gánh nguyên nợ repo ngoài; ranh giới "mượn gì từ đâu" minh bạch ([ARCHITECTURE §6](../ARCHITECTURE.md)).
- Tiêu cực / nợ: phải tự viết lớp keo hợp nhất; cần kỷ luật để không "fork lén" khiến phụ thuộc repo ngoài; ba repo khác stack (FastAPI/Flask/FastAPI) — phải chuẩn hoá khi tái hiện pattern.
- Ảnh hưởng 4 nguyên tắc bất biến: **củng cố** — bảo mật-mặc-định kế thừa arkon; offline kế thừa docsgpt/letta; non-invasive nhờ `requires_approval` + Draft Queue; zero-hallucination nhờ Verify + provenance mở rộng.
- Việc tiếp: các quyết định con (vector store, model, mức MRP, tích hợp ERP) thành ADR riêng (xem backlog [README](README.md)).

## Tham chiếu
Notes chắt lọc: [arkon](../reference/arkon-notes.md), [docsgpt](../reference/docsgpt-notes.md), [letta](../reference/letta-notes.md). Bản đồ truy vết: [ARCHITECTURE.md §6](../ARCHITECTURE.md).
