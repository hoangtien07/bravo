# BRAVO AI Copilot

> **Current-state entrypoint:** read [docs/PROJECT-STATE.md](docs/PROJECT-STATE.md) before using
> progress/test counts below. The worktree is currently dirty and historical green-test counts
> have not been revalidated by the 2026-07-16 documentation cleanup. AI reviewers should follow
> [docs/AI-REVIEW-MANIFEST.md](docs/AI-REVIEW-MANIFEST.md).

> **Enterprise Knowledge & Financial Analytics Hub** — biến BRAVO ERP thành một hệ thống mở thông minh, có khả năng tương tác bằng ngôn ngữ tự nhiên và tự động hoá phân tích, với bảo mật phân quyền cấp phòng ban và sàn vận hành offline 100% (hybrid cloud tuỳ chọn, có kiểm soát).

**Trạng thái:** 🟢 Đang build (Phase 1–2). Lõi đã chạy E2E: RAG có RLS + trích dẫn · agent loop ràng buộc + verify-gate số · **money-engine AP** (hoá đơn điện tử XML → bút toán nháp TT99) · **nền tảng chat** (React SPA + SSE streaming + lịch sử hội thoại). ~140 test xanh.

## Chức năng (đã chạy)

| Nhóm | Mô tả | Surface |
|---|---|---|
| **Hỏi-đáp tri thức** | RAG có RLS theo phòng ban + trích dẫn trang/sheet/ô; từ chối khi ngoài phạm vi | chat · `/api/ask` |
| **Agentic** | Vòng lặp ràng buộc (ADR-0010): chọn tool, verify-gate chống bịa số, egress-audit, draft HITL | chat agentic · `/api/agent/ask` |
| **Money-engine AP** | Hoá đơn điện tử XML → bút toán nháp cân Nợ=Có, map TK **TT99**, VAT 1331, trích dẫn dòng → duyệt (maker-checker) | chat (inline) · panel · `/api/invoices/draft` |
| **Chat platform** | Streaming token + bước agent + citations panel; lịch sử hội thoại theo người dùng; chia sẻ read-only; feedback | React SPA · `/api/chat/{id}/messages` (SSE) |

## Chạy thử (local)

```bash
# 1) Hạ tầng + backend
cp .env.example .env                       # bật cloud-only demo (xem preset trong file) hoặc local LLM
docker compose up -d postgres redis
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_demo.py                # 5 user demo (mật khẩu: demo123)
python scripts/ingest_userguide.py         # nạp corpus cẩm nang (nếu có)

# 2) Frontend React (build 1 lần -> uvicorn tự serve)
cd frontend-react && npm install && npm run build && cd ..

# 3) Chạy
uvicorn app.main:app --port 8000           # http://localhost:8000  (đăng nhập ketoan@bravo.vn / demo123)
```
Dev hot-reload FE: `cd frontend-react && npm run dev` (proxy `/api` → :8000) → http://localhost:5173.
Chi tiết: [README-DEV.md](README-DEV.md).

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
