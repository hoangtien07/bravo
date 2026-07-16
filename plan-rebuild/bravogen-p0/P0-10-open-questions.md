# P0-10 — Open questions

Status: `REFERENCE — unresolved questions carried into R1; R0 collection is complete`

| ID | Question | Why it matters | Test/evidence needed | Status |
|---|---|---|---|---|
| OQ-01 | Ba mode khác corpus/tool hay chỉ khác policy/template? | quyết định product profiles | P0-A cross-mode controls | Open |
| OQ-02 | Citation có claim support thật không? | độ tin cậy câu trả lời | P0-C + mở nguồn | Open |
| OQ-03 | Graph-like output có dữ liệu quan hệ ổn định không? | có cần graph capability | P0-D repeated traversal | Open |
| OQ-04 | Hệ thống có hỏi làm rõ đúng dữ kiện ERP không? | chất lượng tư vấn | T08/T15 | Open |
| OQ-05 | Context correction có loại giả định cũ không? | multi-turn reliability | T13 | Open |
| OQ-06 | Lời “đã tra cứu” của Insight có tương ứng tool execution thật không? | phân biệt retrieval với policy refusal | một câu có nguồn kiểm chứng được + citation/tool surface | Open |
| OQ-07 | Mode boundary có ổn định khi prompt không yêu cầu từ chối rõ không? | loại ảnh hưởng của wording | lặp T01.2 với prompt trung tính, hai phiên | Open |

## Operational constraint observed

Account đang dùng đạt giới hạn tới 14:08 sau ba lượt cross-mode. Không tiếp tục chạy account này trước khi quota mở lại. Cần dùng phiên đăng nhập account thứ hai hoặc tiếp tục theo batch sau 14:08; không lưu token vào research workspace.
## Closed or sharpened after Waves 2–5

- Does graph provenance map to public documents? Still open; internal event IDs were observed.
- Does no-result always terminate? Mostly abstained for fake entities, but several complex graph/policy requests had long streaming latency before completion.
- Does the system carry context across turns? Observed within one conversation; cross-conversation memory was explicitly absent.
- Are policy citations valid? Still open; multiple IDs/URLs remain unaudited or malformed.
