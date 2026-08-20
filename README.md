# BRAVO AI Copilot

> **Current-state entrypoint:** read [docs/PROJECT-STATE.md](docs/PROJECT-STATE.md) before using
> progress/test counts below. Plan 20 is an implementation target, not runtime or production
> evidence. AI reviewers should follow
> [docs/AI-REVIEW-MANIFEST.md](docs/AI-REVIEW-MANIFEST.md).

> **BRAVO Accounting Intelligence** — sản phẩm độc lập để tra cứu tri thức, phân tích và rà soát kế toán trên bằng chứng do người dùng cung cấp. BRAVO là hệ thống ghi nhận bên ngoài: runtime hiện tại không kết nối hoặc thay đổi dữ liệu BRAVO.

**Trạng thái:** Plan 20 implementation in progress. `FigmaMake_UI` là frontend production duy nhất; Import Center, Conversation Core V2, file-backed case và Artifact Workspace vẫn qua các gate riêng.

## Chức năng (đã chạy)

| Nhóm | Mô tả | Surface |
|---|---|---|
| **Knowledge Chat** | Tra cứu tri thức theo RLS, hội thoại, chia sẻ chỉ đọc và feedback | `/api/chat/{id}/messages` (SSE) |
| **Accounting Work** | Bank, Voucher và Period Close case theo deterministic evidence/review contract | `/api/v2/accounting-cases` |
| **Product boundary** | Không có connector BRAVO, journal draft/import export, posting, close hoặc period lock | negative contract tests |

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
Push-Location FigmaMake_UI
corepack enable
pnpm install --frozen-lockfile
pnpm build
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
Set-Location FigmaMake_UI
pnpm dev
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
cd FigmaMake_UI && corepack enable && pnpm install --frozen-lockfile && pnpm build && cd ..
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
