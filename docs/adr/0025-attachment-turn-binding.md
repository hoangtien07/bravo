# 0025. Attachment turn-binding + re-gửi ảnh N lượt gần (có cap)

- **Trạng thái:** Accepted (2026-07-13)
- **Liên quan:** [ADR-0024](0024-sse-protocol-v2.md), [ADR-0022](0022-egress-guard-to-audit.md).

## Bối cảnh

Ảnh đính kèm trước đây chỉ gửi cho vision LLM đúng lượt của nó (`a in current`) → sang lượt sau hỏi tiếp về ảnh thì bot "quên". Nhưng ảnh ở đây là chứng từ/hoá đơn (PII + tài chính); mỗi lần re-gửi lên cloud là một lần **egress lại** cùng dữ liệu nhạy, tiện ích giảm nhanh theo lượt.

## Quyết định

- Thêm `attachments.message_id` (FK `conversation_messages` **ON DELETE SET NULL**) — buộc attachment vào lượt user đã gửi (nền cho truncate/erasure không orphan).
- **Re-gửi ảnh gần đây có CAP CỨNG**: lượt hiện tại + ảnh gần nhất của hội thoại, tối đa `attach_image_max` (mặc định **4**) ảnh/prompt; `attach_image_turns` (mặc định 3) ghi ý định. Vượt cap → bỏ ảnh cũ nhất. Đây là **data-minimization PDPL** (F-2), không phải giới hạn kỹ thuật thuần.
- Mọi lần egress ảnh được audit đầy đủ (actor/session/sha256 từng ảnh — ADR-0024 §5).
- Text đính kèm: re-inject nguyên như cũ (không tốn egress ảnh).

## Hệ quả

- **+** Bot "nhớ" ảnh qua vài lượt mà chi phí/PII-exposure bị chặn trên.
- **−** Cap theo số lượng là xấp xỉ "N lượt" (không join seq/message_id) — đủ cho mục tiêu minimization; có thể siết theo turn-window sau nếu cần.
- Chủ dự án có thể nâng `attach_image_max` nhưng phải chấp nhận nhân bản egress (ghi ở đây).
