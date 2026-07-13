# 0028. Các surface frontier phải fail-closed; GraphRAG cần evidence gate

**Trạng thái:** Accepted
**Ngày:** 2026-07-13

## Quyết định

- Realtime mặc định tắt. API chỉ công bố capability; một session broker được review riêng mới
  được phép cấp transport cho client. Khóa cloud không bao giờ đi vào browser.
- Computer-use mặc định tắt, chỉ có allowlist HTTPS và quyền `computer:use`. Mọi `click`/`type`
  là proposal chờ human approval; BRAVO không cho agent tự thao tác ERP.
- GraphRAG chưa được xây mặc định. `python -m app.eval.graphrag_gate baseline.json candidate.json`
  là cổng quyết định: candidate cần tăng chất lượng relation-heavy, không làm tụt chất lượng tổng,
  đủ mẫu và vẫn nằm trong latency budget.

## Hệ quả

Metadata routing vẫn là đường truy hồi chuẩn. Knowledge graph hiện hữu chỉ là navigation/visualization,
không được gọi là Full GraphRAG. Một đề xuất GraphRAG không vượt gate bị dừng thay vì được bù bằng
thêm infrastructure.
