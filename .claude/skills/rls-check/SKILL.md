---
name: rls-check
description: "Kiểm tra một tính năng/luồng dữ liệu có rò rỉ phân quyền Row-Level Security không. Đi qua mọi đường truy cập dữ liệu và xác minh filter phân quyền được áp ở tầng SQL. Triggers: rls check, kiểm tra phân quyền, có rò dữ liệu không, kiểm tra bảo mật, row level security, ai thấy gì, scope leak."
allowed-tools: Read, Grep, Glob
---

# rls-check: Kiểm tra rò rỉ phân quyền

Mục tiêu: với một tính năng hoặc luồng dữ liệu, truy mọi con đường mà dữ liệu có thể tới tay người dùng và xác minh **không có đường nào trả về dữ liệu ngoài scope phòng ban của họ**.

Đây là kiểm tra nhẹ, làm nhanh trong luồng. Cho thẩm định sâu/đa chiều, dùng `/council-review` (sẽ gọi `security-rls-auditor`).

## Mô hình tham chiếu (Arkon)
RLS của Arkon là khuôn mẫu — đọc khi cần: `../arkon/app/services/permission_engine.py` (`build_document_filter`, `can_access_document`), `../arkon/app/services/mcp_auth_service.py` (`apply_scope_filter`, `ResolvedIdentity`). Xem thêm `docs/SECURITY-RLS.md`.

## Checklist (đi từng đường truy cập)

Liệt kê **mọi** đường dữ liệu của tính năng, rồi với mỗi đường hỏi:

1. **REST API** — filter scope áp trong câu `SELECT` (WHERE) hay sau khi đã `fetchall()` vào RAM? (Phải là trong SQL.)
2. **RAG retrieval / vector search** — truy vấn vector có kèm điều kiện scope (allowed_source_ids / department_ids) ngay trong query không? Hay lấy top-k rồi mới lọc (rò qua ranking/score)?
3. **Embedding / search index** — index có trộn dữ liệu nhiều phòng ban không phân vùng? Một query có thể "chạm" embedding ngoài quyền không?
4. **MCP tools** — token resolve ra scope thế nào? Mỗi tool có tự áp `apply_scope_filter`? Danh sách tool có lộ sự tồn tại tài nguyên ngoài quyền?
5. **Citations / preview / snippet** — đoạn trích dẫn trả về có thể chứa nội dung ngoài scope? Tiêu đề tài liệu nhạy cảm có bị lộ?
6. **Thông báo lỗi / "out of scope"** — báo lỗi có tiết lộ *sự tồn tại* hoặc *nội dung* tài nguyên ngoài quyền? (Chuẩn Arkon: chỉ lộ loại-scope + số lượng, không tiêu đề/nội dung.)
7. **Logs / cache / notifications / draft queue** — dữ liệu có rò qua kênh phụ này không? Cache có key theo identity?
8. **Tài liệu dùng chung (global)** — quy tắc "không gắn phòng ban = dùng chung" có được áp đúng, không vô tình để lộ tài liệu lẽ ra giới hạn?

## Đầu ra
- Bảng: mỗi đường truy cập → ✅ an toàn / ❌ rò + lý do.
- Với mỗi ❌: kịch bản rò cụ thể (user phòng A đọc được gì của phòng B) + cách sửa (áp filter ở SQL như Arkon).
- Kết luận: **AN TOÀN / CÓ RÒ RỈ** + danh sách việc phải sửa trước khi triển khai.
