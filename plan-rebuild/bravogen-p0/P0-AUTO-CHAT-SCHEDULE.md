# P0 automated chat schedule

Status: `ARCHIVED EVIDENCE — scheduled collection is complete; do not resume automatically`

## Objective

Tự động gửi các câu hỏi benchmark P0 tới BravoGen theo đúng mode, tránh dùng một mode cho câu hỏi ngoài phạm vi và tránh lặp request không cần thiết.

## Routing contract

| Intent | Model/mode | Test families |
|---|---|---|
| thao tác Bravo 10, nghiệp vụ kế toán/ERP, quy trình người dùng | `bravo-user-guide` / Bravo User Guide | T01.1, T03, T07, T13, T18 |
| Layout XML, DataSource, schema, database, lỗi kỹ thuật, fabricated technical entity | `bravo-insight` / Bravo Insight | T01.2, T01.3, T04, T06, T08, T15, T17 |
| chính sách nội bộ, ISMS, ATTT, approval/compliance | `isms-advisor` / ISMS Advisor | T01.4, T11, T12, policy variants |
| so sánh boundary | tất cả mode | chỉ P0-A T01/T02/T20 |

Không gửi cùng một prompt sang nhiều mode trừ khi `test_id` là cross-mode. Không suy ra account/profile từ tên tab; chỉ ghi `profile_slot` và mode đã quan sát được.

## Profile slots

| Slot | Account/profile | Mode quan sát | Vai trò |
|---|---|---|---|
| P1 | chưa xác định | Bravo Insight | pilot kỹ thuật hiện tại |
| P2 | chưa xác định | chưa xác định | User Guide queue |
| P3 | chưa xác định | chưa xác định | Insight queue |
| P4 | chưa xác định | chưa xác định | ISMS queue |
| P5 | chưa xác định | chưa xác định | cross-mode/stability queue |

Profile chỉ được dùng sau khi thấy trang BravoGen và mode tương ứng. Không tự đăng nhập Google hoặc nhập mật khẩu/OTP.

## Queue order

### Wave 0 — smoke/pilot

1. P1 / `T08.1` — câu hỏi mơ hồ về lỗi Layout XML, yêu cầu liệt kê dữ kiện thiếu. **Complete**; conversation `a493e186-1cf7-4247-8f6e-54e6a52a138d`.
2. Ghi raw output và xác nhận trạng thái hoàn tất. **Complete**.
3. Nếu mode không đúng hoặc quota/error, dừng slot và không retry mù. **No error**.

### Wave 1 — P0-A mode boundary

- `T01.1` User Guide: hướng dẫn lập Phiếu nhập mua trong nước.
- `T01.2` Insight: thuộc tính XML giả/hợp lý, yêu cầu không suy đoán.
- `T01.3` Insight: schema/table Phiếu nhập mua, phân biệt direct/inferred.
- `T01.4` ISMS: cài phần mềm lên production.
- `T02` cùng một câu hỏi quan hệ chứng từ trên ba mode.
- `T20` ba câu cross-domain leakage.

### Wave 2 — P0-B retrieval/hallucination

- `T03.1–T03.3`: bằng chứng trực tiếp và no-general-knowledge.
- `T04.1–T04.5`: XML/field/process/voucher/version giả.
- `T08.1–T08.3`: ambiguity clarification.
- `T15`: refusal khi bị ép đoán.
- `T17`: no-result/tool-failure behavior.

## Per-message state machine

```text
select verified profile
  -> verify current mode
  -> send one prompt
  -> wait for assistant completion
  -> capture raw output + URL + timestamp
  -> classify OBSERVED/INFERRED/UNVERIFIED
  -> enqueue next prompt only if no error/quota
```

## Safety and quota

- Chỉ dùng prompt không có dữ liệu khách hàng.
- Không gửi credential, system-prompt extraction, prompt injection hoặc yêu cầu dữ liệu ngoài quyền.
- Mỗi profile tối đa một request đang chạy; không nhân bản cùng một prompt.
- Khi thấy quota, 401/403, CAPTCHA hoặc login screen: dừng slot và ghi trạng thái.
- Không lưu token/cookie vào workspace.

## Current browser state

Ngày 2026-07-15, connector đã nhận diện 5 Chrome extension instances/profile riêng và mỗi profile có một tab BravoGen. Mode đã đặt và xác nhận:

- P1: Bravo Insight — T04.1 complete.
- P2: Bravo User Guide — T03.1 complete.
- P3: Bravo Insight — T08.2 complete.
- P4: ISMS Advisor — T01.4 complete; citation pending audit.
- P5: Bravo User Guide — T01.1 complete; citation pending audit.

Raw output nằm trong `P0-12-wave1-parallel-run.md`; run index nằm trong `P0-02-raw-test-log.md`. Không lưu token/cookie.
