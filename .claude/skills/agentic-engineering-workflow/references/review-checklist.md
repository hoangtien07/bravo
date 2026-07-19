# Review checklist — theo thứ tự

> Reviewer chỉ cần: yêu cầu đã xác nhận, acceptance criteria, diff, test evidence, code liên quan.
> Phân loại mỗi finding: severity (blocker/major/minor/nit) + evidence (confirmed/plausible/speculative).

## 1. Requirements
- [ ] Diff giải quyết đúng acceptance criteria của issue?
- [ ] Có scope creep — thay đổi ngoài phạm vi issue?
- [ ] Quyết định đã chốt trong PRD/brief có bị làm trái không?

## 2. Tests (review TRƯỚC implementation)
- [ ] Test kiểm tra đúng hành vi mong muốn, không phải khớp implementation?
- [ ] Có bằng chứng test thất bại trước khi sửa (TDD)?
- [ ] Negative case và boundary case có đủ không?
- [ ] Có test nào bị làm yếu, skip, hoặc xóa để đạt pass?

## 3. Correctness
- [ ] Logic đúng với happy path và các nhánh lỗi?
- [ ] Regression: hành vi hiện hữu nào có thể bị phá?
- [ ] Race condition, idempotency, trạng thái trung gian?

## 4. Security
- [ ] Authorization/tenant isolation áp ở đúng tầng (SQL, không phải RAM)?
- [ ] Mọi entry point bị ảnh hưởng đã kiểm tra (HTTP / agent / MCP / worker / connection pool)?
- [ ] Input validation, injection, dữ liệu nhạy cảm rò ra log/response?

## 5. Data & migrations
- [ ] Migration an toàn với dữ liệu hiện hữu? Đảo ngược được?
- [ ] Toàn vẹn dữ liệu (constraint, transaction boundary)?

## 6. API compatibility
- [ ] Public API/contract có breaking change không? Nếu có — đã được chốt chưa?

## 7. Frontend behavior
- [ ] Loading / empty / error / success states?
- [ ] Đã quan sát thực tế hay chỉ build pass? Cần human visual QA không?

## 8. Observability
- [ ] Lỗi có log đủ context để debug production?
- [ ] Metric/trace cần thiết có được thêm không?

## 9. Documentation
- [ ] Tài liệu vận hành cập nhật nếu hành vi đổi?
- [ ] PRD/plan được đánh dấu completed/superseded?

## 10. Residual risks
- [ ] Kiểm tra nào chưa chạy được, vì sao, rủi ro còn lại?
- [ ] Unresolved risk nào cần thành issue mới?
