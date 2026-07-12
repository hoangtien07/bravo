# 0026. Edit / regenerate tuyến tính (truncate + audit), CHƯA branching

- **Trạng thái:** Accepted (2026-07-13) — quyết định chốt; **hiện thực HOÃN sau GATE parity** (xem plan v2.1).
- **Liên quan:** [ADR-0024](0024-sse-protocol-v2.md) (cột `seq`, `message_id`).

## Bối cảnh

Người dùng frontier mong "sửa câu hỏi / hỏi lại" (edit + regenerate). assistant-ui hỗ trợ cả tuyến tính lẫn cây nhánh (branching). `ConversationMessage` không có `parent_id`/`branch_id`; summary cache (ADR-0024) theo prefix; SharedPage/export đều đọc theo thứ tự tuyến tính.

## Quyết định

**Làm TUYẾN TÍNH trước (truncate + re-run), defer branching.**

- Endpoint `POST /conversations/{id}/truncate {from_message_id, inclusive}` (RLS owner), chạy dưới khoá per-conversation (ADR-0024). Cắt theo **`seq`** (không phải `created_at` — tie không phát hiện được với DELETE).
- **Soft-delete ưu tiên** (`deleted_at`, lọc mọi đường đọc) + **AuditLog** `{actor, session, message_ids, content_sha256[], count}` cho cả truncate lẫn `delete_conversation` — sửa câu hỏi sau khi đã nhận trả lời KHÔNG được xoá sạch dấu vết tuân thủ (F-3).
- Cùng transaction: xoá `summary`/`summary_upto` MemoryBlock (reset watermark — khớp B1 S3).
- Orphan: Draft của lượt bị cắt → annotate/auto-reject qua `agent_run_id`; text attachment của lượt bị cắt → clear `conversation_id` (không thì re-inject mãi); hội thoại đã share bị truncate → rotate token/cảnh báo.
- Edit v1 text-only (attachment gốc rơi theo SET NULL — toast cảnh báo).

**Đường nâng cấp branching giữ mở:** thêm `parent_id` nullable + `ExportedMessageRepository.fromBranchableArray` là additive; không phải làm lại.

## Hệ quả

- **+** Tránh migration + rework ordering mà branching đòi; hợp nhu cầu helpdesk.
- **+** Dấu vết edit được kiểm toán (không mất bản ghi tuân thủ).
- **−** Chưa có cây hội thoại — chấp nhận cho tới khi có nhu cầu thật.
