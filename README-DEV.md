# BRAVO AI Copilot — Developer Guide

> **Freshness:** setup reference for the existing platform. Read
> [docs/PROJECT-STATE.md](docs/PROJECT-STATE.md) before assuming current phase, test status, or
> active architecture work. `docs/PLAN.md` is now a historical implementation plan.

Stack: FastAPI + async SQLAlchemy + PostgreSQL/pgvector (modular monolith — [ADR-0007](docs/adr/0007-code-strategy.md)).

## Chạy nhanh (dev)
```bash
cp .env.example .env            # bật preset DEMO CLOUD-ONLY (OpenAI) hoặc LLM local
docker compose up postgres redis -d
pip install -e ".[dev]"         # core = cloud-only nhẹ; `.[local]` = bge-m3/Docling (cần GPU/bake)
python -m alembic upgrade head
python -m scripts.seed_demo      # 5 tài khoản demo (mật khẩu demo123) + token MCP demo
python -m scripts.seed_content   # 4 bút toán nháp mẫu (màn hình không rỗng khi test)
# Tài khoản: giamdoc(admin) · ketoan(maker) · ketoantruong(checker+MCP) · kinhdoanh · nhansu(HR)
# Luồng admin BE+FE + checklist test nội bộ: docs/ADMIN-FLOW-PLAN.md

# Frontend React (Vite). Build 1 lần -> uvicorn serve dist ở /static + SPA-fallback:
cd frontend-react && npm install && npm run build && cd ..
uvicorn app.main:app --port 8000 --reload   # http://localhost:8000  (--reload: code mới có hiệu lực ngay)

# Hoặc dev hot-reload FE (2 cổng):
cd frontend-react && npm run dev      # http://localhost:5173 (proxy /api -> :8000)
```
Nếu bạn chạy các lệnh này trong PowerShell trên máy host và `.env` vẫn trỏ `postgres`, set tạm DSN trước khi migrate/seed:

```powershell
$env:DATABASE_URL = 'postgresql+asyncpg://bravo:bravo@localhost:5432/bravo'
python -m alembic upgrade head
python -m scripts.seed_demo
python -m scripts.seed_content
```
> ⚠ **Đính kèm chat (attachments) & ingest bất đồng bộ:** upload docx/pdf được enqueue cho arq worker.
> Ở dev một-tiến-trình, HOẶC đặt `INGEST_SYNC=true` trong `.env` (bóc tách inline, không cần worker),
> HOẶC chạy worker: `docker compose up worker` (đã định nghĩa sẵn). Không có cả hai thì attachment
> docx/pdf sẽ kẹt ở trạng thái `pending`. Ảnh & .txt/.md nhỏ luôn xử lý inline (không cần worker).
> LUÔN chạy uvicorn với `--reload` khi dev để tránh backend phục vụ route cũ (thiếu `/api/attachments`).
LLM cục bộ (Qwen2.5) chạy riêng qua vLLM/Ollama (OpenAI-compatible) ở `LLM_LOCAL_BASE_URL`. Demo dùng cloud OpenAI (preset trong `.env.example`). Health: `/livez` (process), `/readyz` (DB+catalog).

## Cấu trúc (modular monolith)
```
app/
  config.py          # Pydantic settings + validate_boot (fail-closed prod)
  database/          # engine, session, ORM models (Conversation, Draft, AgentRun, Chunk…)
  security/          # rls.py (RLS-on-vector + conversation_scope_filter), auth.py (JWT)
  ingestion/         # parser (Docling) -> chunker -> pipeline; invoice_parser.py (hoá đơn XML)
  rag/               # embedding (bge-m3/cloud + egress-guard), retriever (hybrid + RLS)
  llm/               # router.py (Model Router: local default, cloud opt-in, audit-then-egress)
  data_layer/        # semantic (metric), calc (sandbox), grounding (verify-gate), money (Decimal)
  accounting/        # [money-engine] coa (TT99), crosswalk, account_mapper, journal, ap_service
  agent/             # loop.py (step + step_stream SSE), memory, runs (durable), conversations
  erp/               # draft_queue (non-invasive, maker-checker)
  api/               # routes: auth·ask·agent·conversations(SSE)·invoices·drafts·sources
  main.py            # FastAPI app + SPA serve (frontend-react/dist) + livez/readyz
  worker.py          # arq ingestion worker
frontend-react/      # React+Vite+TS+Tailwind SPA (chat streaming, sidebar, money-engine, share)
alembic/versions/    # 0001..0005 (init, memory, agentrun, db-roles, conversations)
```

## Bốn nguyên tắc bất biến — đã gài vào code
1. **RLS tầng SQL:** `app/security/rls.py::chunk_scope_filter` áp scope *trong* truy vấn vector. Không lọc post-retrieval.
2. **Không xâm lấn:** ERP read-only; ghi = `Draft` chờ duyệt (`app/erp/`, `app/agent/tools.py`).
3. **Zero-hallucination:** `routes_ask` từ chối khi không có ngữ cảnh; trích dẫn provenance; số liệu → data_layer (LLM không tính — Phase 2).
4. **Chủ quyền dữ liệu:** `app/llm/router.py` mặc định local, fail-closed; dữ liệu nhạy ghim local.

## Nạp corpus & chạy thử (BRAVO 10 user guide — KB MVP)
```bash
python -m scripts.seed                 # phòng ban + user mẫu
python -m scripts.ingest_userguide     # nạp 19 cẩm nang BRAVO 10 (UserGuide_B10_TV_PDF/)
```
**Chạy 2 giai đoạn để có kết quả nhanh:**
1. **Retrieval-only (KHÔNG cần LLM/GPU):** chỉ cần Postgres + `bge-m3`. Test truy hồi+trích dẫn (đúng chương/trang) — chứng minh lõi RLS+RAG chạy trên dữ liệu thật.
2. **Full Q&A:** thêm LLM cục bộ (Qwen2.5 qua vLLM/Ollama) → `/api/ask` trả lời ngôn ngữ tự nhiên có dẫn chứng.

## Migrations
```bash
alembic revision --autogenerate -m "init"   # cần CREATE EXTENSION vector; trong migration đầu
alembic upgrade head
```
> Lưu ý: migration đầu phải `CREATE EXTENSION IF NOT EXISTS vector;` trước khi tạo cột Vector.

## Trạng thái (branch)
- ✅ **main-ish**: RLS+auth, ingestion, RAG retriever, Model Router, agent loop + verify-gate, eval pass^k, draft HITL.
- ✅ **feat/money-engine-ap**: nạp catalog runtime, bịt egress, CoA TT99 + parser hoá đơn XML + journal validator (Nợ=Có, ADR-0014), endpoint AP + UI, AgentRun durable, observability, CI, DB-role.
- ✅ **feat/chat-platform** (HEAD): hội thoại + SSE streaming + multi-turn (ADR-0015), React SPA, share/feedback.
- ⏳ Tiếp: real ERP DataSource, real-loop pass^k blocking, httpOnly cookie auth, kế toán ký-nhận rule map TT99.

## Test & CI
```bash
# 1) Cài dev deps vào venv (pytest/ruff/mypy). Với uv:
VIRTUAL_ENV=.venv uv pip install pytest pytest-asyncio ruff mypy   # hoặc: pip install -e ".[dev]"

# 2) Postgres phải chạy + đã migrate. Khi chạy pytest TRỰC TIẾP (không trong container),
#    DATABASE_URL phải trỏ 'localhost' (host 'postgres'/'redis' chỉ resolve trong docker network).
docker compose up postgres redis -d
export DATABASE_URL="postgresql+asyncpg://bravo:bravo@localhost:5432/bravo"
alembic upgrade head

# 3) Chạy suite — kỳ vọng: 157 passed, 5 skipped (ragas/docling importorskip cho tới khi cài .[local]/ragas)
pytest -q
python -m app.eval.run --passk --mock --k=8 # eval HARD-FAIL gate (deterministic)
cd frontend-react && npm run build          # tsc + vite (typecheck FE)
```

### Docker-only PostgreSQL integration tests

Use this path when the host environment should not publish PostgreSQL or rewrite its
`DATABASE_URL`. The test container shares PostgreSQL's network namespace, so legacy DB probes
and the application engine exercise the same local database without exposing a host port.

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d postgres
docker compose -f docker-compose.yml -f docker-compose.test.yml build test
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm --no-deps test alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm --no-deps test python -m scripts.seed_demo
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm --no-deps test python -m pytest -q -rs
```

The `test` target includes development dependencies only; the production `api` and `worker`
images remain unchanged.

> ⚠️ Nếu KHÔNG export `DATABASE_URL=...localhost...`, 7 test DB-integration sẽ **FAIL** (không phải skip):
> probe `_db_available()` dò `localhost` (docker map port → thấy mở) nhưng engine đọc `get_settings().database_url`
> = host `postgres` từ `.env` → lỗi name-resolution. Đây là ranh giới dev-env, không phải bug code.
>
> CI: `.github/workflows/ci.yml` (ruff **blocking** + pytest với **Postgres service** + eval gate). Trong CI
> `DATABASE_URL` trỏ service `postgres` và `alembic upgrade head` chạy trước pytest → test DB-integration CHẠY thật.
