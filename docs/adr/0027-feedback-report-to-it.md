# 0027. Feedback mở rộng: comment + category (report-to-IT)

> Canonical index alias: **ADR-0027a**. A historical filename-number collision also produced
> ADR-0027b; see [ADR index](README.md).

- **Trạng thái:** Accepted (2026-07-13)
- **Liên quan:** [ADR-0024](0024-sse-protocol-v2.md).

## Bối cảnh

Chat mới có like/dislike nhị phân (`ConversationMessage.feedback`). Người dùng cần **báo lỗi cho đội IT** để cải thiện phần mềm (yêu cầu chủ dự án). Council 2026-07-12 #4: dislike phải nuôi được golden set.

## Quyết định

- Thêm cột `conversation_messages.feedback_comment TEXT` + `feedback_category VARCHAR(32)` (một report/message là đủ cho triage nội bộ — cột thay vì bảng riêng).
- Endpoint feedback nhận `{value, comment?, category?}`; category ∈ `{wrong_number, wrong_source, unhelpful, bug, other}` (ngoài danh sách → `other`); comment cap 2000 ký tự (F-9).
- `scripts/export_feedback.py`: dùng `yaml.safe_dump` (không tự escape tay), xuất kèm comment/category, **header cảnh báo PDPL** (có thể chứa dữ liệu cá nhân, chỉ IT, đặt retention).

## Hệ quả

- **+** Vòng phản hồi end-user → IT → golden set/corpus khép kín.
- **−** Free-text có thể chứa PII → phải giới hạn quyền chạy script + retention (PDPL). Ghi ở header + ADR.
