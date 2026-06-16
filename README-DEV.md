# BRAVO AI Copilot — Developer Guide

Hiện thực theo [docs/PLAN.md](docs/PLAN.md). Stack: FastAPI + async SQLAlchemy + PostgreSQL/pgvector (modular monolith — [ADR-0007](docs/adr/0007-code-strategy.md)).

## Chạy nhanh (dev)
```bash
cp .env.example .env            # bật preset DEMO CLOUD-ONLY (OpenAI) hoặc LLM local
docker compose up postgres redis -d
pip install -e ".[dev]"         # core = cloud-only nhẹ; `.[local]` = bge-m3/Docling (cần GPU/bake)
alembic upgrade head
python scripts/seed_demo.py     # 5 user demo (mật khẩu demo123)

# Frontend React (Vite). Build 1 lần -> uvicorn serve dist ở /static + SPA-fallback:
cd frontend-react && npm install && npm run build && cd ..
uvicorn app.main:app --port 8000     # http://localhost:8000

# Hoặc dev hot-reload FE (2 cổng):
cd frontend-react && npm run dev      # http://localhost:5173 (proxy /api -> :8000)
```
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
pytest -q                                   # ~140 test (DB-integration skip nếu Postgres tắt)
python -m app.eval.run --passk --mock --k=8 # eval HARD-FAIL gate (deterministic)
cd frontend-react && npm run build          # tsc + vite (typecheck FE)
```
CI: `.github/workflows/ci.yml` (ruff + pytest + eval gate).
