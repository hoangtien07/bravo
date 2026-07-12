# 0024. Giao thức SSE chat v2 + hạ tầng an toàn cho lượt chat

- **Trạng thái:** Accepted (2026-07-13)
- **Ngày:** 2026-07-13
- **Liên quan:** [ADR-0022](0022-egress-guard-to-audit.md) (egress audit), [ADR-0025](0025-attachment-turn-binding.md) (turn-binding ảnh), [ADR-0027](0027-feedback-report-to-it.md) (feedback/report).

## Bối cảnh (Context)

Nền chat v2 (SSE POST+fetch) thiếu vài mắt xích để lên chuẩn "frontier chatbot" và để an toàn vận hành (audit BE 4 chiều, 2026-07-13):
- Sự kiện `done` KHÔNG mang `message_id` của câu trả lời đã lưu → client không gắn được like/dislike/sửa mà không phải refetch.
- Không có khoá per-conversation → hai lượt gửi đồng thời cùng một hội thoại ghi xen kẽ history/summary (rủi ro S5/S6).
- Lượt tài chính buffered (verify-gate, invariant #3) không phát token nào cho tới khi có cả khối → UI trông như treo.
- Egress audit chỉ có `prompt_hash`, không trả lời được "ẢNH của AI nào đã rời mạng, mấy lần" (SECURITY-RLS §9.4, F-1).
- `/shared` không rate-limit, không có nút thu hồi (F-4).

## Quyết định (Decision)

**Nâng giao thức SSE lên v2 + thêm hạ tầng an toàn, KHÔNG phá tương thích client cũ (chỉ THÊM field/event).**

1. **`done` mang message ids:** `recall_add` trả `row.id`; `done` thêm `message_id` (assistant) + `user_message_id`. Client gắn feedback/edit trực tiếp.
2. **Event `status`** `{type:"status", text}`: phát ở ranh giới xử lý — đặc biệt `"Đang kiểm tra số liệu..."` khi vào verify-gate buffered (lượt tài chính không còn trông như treo).
3. **Reserve (đặt chỗ, CHƯA phát) các event tương lai:** `plan` / `plan_update` / `subtask` (agent planner), `reasoning` (chain-of-thought stream), `artifact`. Client build switch forward-compatible; server bổ sung sau là drop-in.
4. **Khoá per-conversation** (`asyncio.Lock` theo `session_id`): lượt thứ hai đồng thời trên cùng hội thoại nhận `error{code:"busy"}`. **In-process** cho single-worker; **multi-worker prod PHẢI dùng `pg_advisory_xact_lock(hashtext(session_id))`** (chưa build — điều kiện trước khi scale worker). Map khoá tự dọn entry rảnh (F-12).
5. **Egress audit đầy đủ (F-1):** `_audit_egress` ghi thêm `actor_id`, `session_id`, và sha256 **từng ảnh** (`image_sha256[]` + `image_count`), truyền từ agent loop. Trả lời được câu hỏi tuân thủ "ảnh của ai đã egress mấy lần".
6. **Share governance:** `DELETE /conversations/{id}/share` (thu hồi/rotate token về None); `@limiter` trên `/shared`.
7. **Cột `seq`** (BIGINT sequence-backed, backfill theo `created_at`) trên `conversation_messages` — thứ tự tuyệt đối không đụng độ, nền cho truncate/edit (ADR-0026). Migration `0011_sse_v2` (idempotent guards).

## Hệ quả (Consequences)

- **+** Feedback-live, report-to-IT, và edit/regenerate (ADR-0026) đều mở khoá nhờ `message_id`.
- **+** Bằng chứng tuân thủ PDPL cho ảnh; UI không còn "đơ" ở lượt tài chính.
- **−** Khoá in-process CHƯA đủ cho multi-worker — đã ghi là điều kiện chặn trước khi scale.
- **−** `done` to hơn (2 field id) — không đáng kể; client cũ bỏ qua field lạ.
- Migration 0011 additive (nullable FK + cột) → rollback = `downgrade -1`.
