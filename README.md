# BRAVO AI Copilot

> **Enterprise Knowledge & Financial Analytics Hub** — biến BRAVO ERP thành một hệ thống mở thông minh, có khả năng tương tác bằng ngôn ngữ tự nhiên và tự động hoá phân tích, với bảo mật phân quyền cấp phòng ban và sàn vận hành offline 100% (hybrid cloud tuỳ chọn, có kiểm soát).

**Trạng thái:** 🟡 Giai đoạn thiết kế (design phase) — chưa code.

## Đọc theo thứ tự

1. [docs/VISION.md](docs/VISION.md) — mục tiêu dự án (đã tinh chỉnh) & định vị thị trường
2. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — kiến trúc đề xuất, tổng hợp từ 3 repo tham chiếu
3. [docs/SECURITY-RLS.md](docs/SECURITY-RLS.md) — mô hình phân quyền & bảo mật
4. [docs/ROADMAP.md](docs/ROADMAP.md) — lộ trình theo giai đoạn
5. [docs/GLOSSARY.md](docs/GLOSSARY.md) — thuật ngữ
6. [docs/adr/](docs/adr/) — các quyết định kiến trúc (ADR)
7. [docs/research/findings/SUMMARY.md](docs/research/findings/SUMMARY.md) — **tổng hợp deep research** (cạnh tranh, học thuật, lỗi triển khai, thị trường VN, pháp lý) + 10 hành động ưu tiên

## Repo tham chiếu (chỉ để học, không sửa)

- `../arkon` — RLS/RBAC + biên soạn wiki có trích dẫn + workflow duyệt
- `../docsgpt` — nạp đa định dạng + bóc tách bảng + RAG offline
- `../letta` — bộ nhớ agent có trạng thái + tool-calling

Notes chắt lọc: [docs/reference/](docs/reference/).

## Làm việc với AI

Repo được trang bị sẵn Claude harness: xem [CLAUDE.md](CLAUDE.md). Hội đồng cố vấn ở [.claude/agents/](.claude/agents/), skills ở [.claude/skills/](.claude/skills/).
