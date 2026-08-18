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

Yêu cầu: Docker Desktop đang chạy, Node.js 20+ và Python 3.11–3.14. Dùng Python 3.11–3.13 nếu
cần toàn bộ bộ dev/eval; Python 3.14 chạy được ứng dụng và migration, nhưng phần `ragas` được bỏ
qua. Trên Windows, kiểm tra các bản Python có sẵn bằng `py -0p` và **dùng cùng một bản Python cho
tất cả lệnh bên dưới**. Ví dụ này dùng Python 3.14; thay `3.14` bằng bản bạn đã chọn.

### Windows / PowerShell

```powershell
# 1) Tạo cấu hình local nếu chưa có. Không commit file .env.
if (-not (Test-Path .env)) { Copy-Item .env.example .env }

# 2) Khởi động hạ tầng; chờ postgres có trạng thái healthy.
docker compose up -d postgres redis
docker compose ps

# 3) Host PowerShell phải dùng localhost: hostname "postgres" chỉ có trong Docker network.
$env:DATABASE_URL = 'postgresql+asyncpg://bravo:bravo@localhost:5432/bravo'

# 4) Cài dependency, tạo schema, rồi nạp tài khoản demo.
py -3.14 -m pip install -e ".[dev]"
py -3.14 -m alembic upgrade head
py -3.14 -m alembic current                 # kỳ vọng: 0020_case_v2_audit (head)
py -3.14 -m scripts.seed_demo

# 5) Build frontend và chạy backend.
Push-Location frontend-react
npm install
npm run build
Pop-Location
py -3.14 -m uvicorn app.main:app --port 8000 --reload
```

Mở http://localhost:8000 và đăng nhập `ketoan@bravo.vn` / `demo123`.

Nạp cẩm nang là bước tùy chọn, chỉ chạy sau khi migration và seed đã thành công:

```powershell
$env:DATABASE_URL = 'postgresql+asyncpg://bravo:bravo@localhost:5432/bravo'
py -3.14 -m scripts.ingest_userguide
```

Dev hot-reload frontend chạy ở terminal khác:

```powershell
Set-Location frontend-react
npm run dev
```

Sau đó mở http://localhost:5173; Vite sẽ proxy `/api` đến backend ở cổng 8000.

### macOS / Linux

Thay `py -3.14` bằng Python đã chọn, ví dụ `python3.13`, và dùng cùng URL database cho phiên shell:

```bash
test -f .env || cp .env.example .env
docker compose up -d postgres redis
export DATABASE_URL='postgresql+asyncpg://bravo:bravo@localhost:5432/bravo'
python3.13 -m pip install -e ".[dev]"
python3.13 -m alembic upgrade head
python3.13 -m scripts.seed_demo
cd frontend-react && npm install && npm run build && cd ..
python3.13 -m uvicorn app.main:app --port 8000 --reload
```

### Xử lý lỗi local thường gặp

- `No module named alembic.__main__` hoặc `No module named alembic`: bạn đang gọi một Python khác
  với Python đã cài dependency. Trên Windows, dùng lại chính `py -3.14 -m ...` (hoặc bản đã chọn),
  không gọi `alembic`/`uvicorn` trực tiếp.
- `could not translate host name "postgres"`: lệnh đang chạy trên host nhưng `DATABASE_URL` chưa
  được override cho phiên shell. Chạy lại lệnh `$env:DATABASE_URL = ...localhost...` ở trên.
- Migration phải kết thúc ở `0020_case_v2_audit (head)` trước khi chạy `seed_demo` hoặc ingest.
  Không chạy các lệnh sau nếu migration thất bại.
- Nếu đây chỉ là database demo local, chưa có dữ liệu cần giữ, và một lần chạy cũ đã làm migration
  dở dang, khởi tạo lại volume rồi lặp lại toàn bộ hướng dẫn Windows/macOS/Linux ở trên:

  ```powershell
  # XÓA toàn bộ database Docker local của project, không dùng cho dữ liệu cần giữ.
  docker compose down -v
  docker compose up -d postgres redis
  ```

Chi tiết cho development và test: [README-DEV.md](README-DEV.md).

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
