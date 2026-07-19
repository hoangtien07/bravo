# PRD / Remediation Brief — [Tên feature hoặc finding]

> Điền ngắn gọn. PRD mô tả **đích đến và ràng buộc đã xác nhận**, không phải nhật ký hội thoại.
> Với remediation brief: "Problem statement" = finding + evidence, "Acceptance criteria" = exit criteria để đóng blocker.

## Metadata
- **Loại:** [PRD | Decision brief | Remediation brief]
- **Ngày:** [YYYY-MM-DD]
- **Trạng thái:** [draft | confirmed | in-progress | completed | superseded]
- **Liên quan:** [ADR, issue, audit finding, tài liệu nguồn]

## 1. Problem statement
[Vấn đề gì, ai đau, tại sao bây giờ. Với remediation: mô tả finding và mức độ nghiêm trọng.]

## 2. Mục tiêu
[Kết quả quan sát được khi hoàn thành. Đo được nếu có thể.]

## 3. Non-goals
[Những gì cố tình KHÔNG làm trong phạm vi này.]

## 4. Actors & user stories
[Ai dùng/bị ảnh hưởng. Mỗi story: "Là [actor], tôi muốn [hành vi] để [giá trị]."]

## 5. Luồng nghiệp vụ
[Happy path + các nhánh chính. Sơ đồ text nếu giúp làm rõ.]

## 6. Quy tắc nghiệp vụ
[Rule bất biến, ràng buộc domain. Đánh số để issue tham chiếu.]

## 7. Dữ liệu & migration
[Schema mới/thay đổi. Migration path. Backward compatibility. Dữ liệu hiện hữu xử lý ra sao.]

## 8. Security / authorization
[Ai được thấy/làm gì. Filter áp ở tầng nào. Entry point nào bị ảnh hưởng (HTTP / agent / MCP / worker / pool).]

## 9. Failure modes
[Điều gì có thể hỏng, hệ thống phản ứng ra sao, user thấy gì.]

## 10. Observability
[Log/metric/trace nào cần có để biết feature chạy đúng trong production.]

## 11. Acceptance criteria
[Danh sách kiểm chứng được. Mỗi mục: hành vi + cách xác minh.]

## 12. Testing strategy
[Tầng test nào (unit/integration/E2E), boundary nào cần test, dữ liệu test lấy từ đâu.]

## 13. Rollback considerations
[Cách quay lui nếu hỏng. Migration có đảo ngược được không.]

## 14. Open questions
[Chưa chốt — chặn triển khai phần nào.]

## 15. Decisions confirmed
[Quyết định người dùng đã chốt, kèm ngày. Phân biệt với assumption.]

## 16. Evidence / source references
[`path:line`, tài liệu, ADR làm căn cứ cho các fact trong PRD này.]
