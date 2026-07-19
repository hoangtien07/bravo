# Issue — [ID] [Tiêu đề ngắn, mô tả hành vi]

> Một issue = một vertical slice: hành vi nhỏ nhưng hoàn chỉnh, kiểm thử độc lập được.

- **Trạng thái:** [ready | blocked | in progress | completed]
- **Execution mode:** [human-in-loop | AFK-safe]
- **PRD/brief liên quan:** [link hoặc đường dẫn]

## Outcome
[Hành vi user-visible hoặc system-visible khi issue xong. Một câu, quan sát được.]

## Scope
[Những gì issue này làm.]

## Out of scope
[Những gì cố tình để lại cho issue khác.]

## Dependencies
[Issue nào phải xong trước. "None" nếu độc lập — chỉ khi thực sự độc lập.]

## Files / modules dự kiến
[Danh sách `path` dự kiến chạm tới. Cập nhật khi triển khai nếu lệch.]

## Acceptance criteria
[Mỗi mục kiểm chứng được:]
- [ ] [Hành vi X xảy ra khi Y]
- [ ] [Negative case: Z bị từ chối/báo lỗi đúng cách]

## Test plan
[Test nào viết mới, test nào cập nhật. TDD: test viết trước, xác nhận fail đúng lý do.]

## Verification commands
```bash
# lệnh chạy test/lint/build để chứng minh issue xong
```

## Security / data considerations
[Phân quyền, tenant isolation, PII, migration. "None" nếu thật sự không chạm — nêu lý do.]

## Completion evidence
[Điền khi xong: output test, diff summary, screenshot nếu là UI. Không có evidence = chưa xong.]
