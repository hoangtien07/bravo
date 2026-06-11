# BRAVO AI Copilot — Developer Guide

Hiện thực theo [docs/PLAN.md](docs/PLAN.md). Stack: FastAPI + async SQLAlchemy + PostgreSQL/pgvector (modular monolith — [ADR-0007](docs/adr/0007-code-strategy.md)).

## Chạy nhanh (dev)
```bash
cp .env.example .env            # điền JWT_SECRET, MCP_TOKEN_PEPPER
docker compose up postgres redis -d
pip install -e ".[dev]"
alembic upgrade head            # (sau khi tạo migration đầu — xem dưới)
uvicorn app.main:app --reload   # http://localhost:8000/health
```
LLM cục bộ (Qwen2.5-32B) chạy riêng qua vLLM/Ollama (OpenAI-compatible) ở `LLM_LOCAL_BASE_URL`; bỏ comment service `vllm` trong `docker-compose.yml` khi có GPU.

## Cấu trúc (modular monolith)
```
app/
  config.py          # Pydantic settings
  database/          # engine, session, ORM models (scope baked in cho RLS)
  security/          # rls.py (RLS-on-vector), auth.py (JWT, perms, MCP token hash)
  ingestion/         # parser (Docling, digital-only, NO OCR) -> chunker -> pipeline
  rag/               # embedding (bge-m3), retriever (RLS-on-vector + hybrid + rerank)
  llm/               # router.py (Model Router: local default, cloud opt-in fail-closed)
  data_layer/        # [Phase 2] semantic (metric layer), calc (PoT sandbox), grounding
  agent/             # [Phase 2] lean memory (MemGPT pattern), tools (requires_approval)
  erp/               # [Phase 2/3] read-only client, draft_queue (non-invasive)
  api/               # routers (auth, ask)
  main.py            # FastAPI app
  worker.py          # arq ingestion worker
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

## Trạng thái
- ✅ Phase 0 (nền tảng) + lõi Phase 1 (RLS, auth, ingestion skeleton, RAG retriever, ask endpoint, Model Router).
- 🔜 Phase 1B/1C: provenance mapping trong parser, BM25+rerank trong retriever, eval.
- ⏳ Phase 2+: data_layer, agent, erp (skeleton sẵn, gắn ADR).
