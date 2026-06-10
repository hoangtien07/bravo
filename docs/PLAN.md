# PLAN — Kế hoạch triển khai chi tiết (task-level)

> Biến [ROADMAP.md](ROADMAP.md) thành các task code cụ thể, bám [ADR](adr/) + [research/findings](research/findings/SUMMARY.md). Cập nhật tiến độ bằng `[x]`. Stack: FastAPI + async SQLAlchemy + PostgreSQL/pgvector (modular monolith — [ADR-0007](adr/0007-code-strategy.md)).

## Nguyên tắc thực thi
- **arkon = viết lại từ pattern** (không copy code — [ADR-0008](adr/0008-arkon-license-ownership.md)); docsgpt/letta = chuyển thể code (MIT/Apache).
- Mỗi tính năng chạm dữ liệu → qua `/rls-check`. Mỗi quyết định lớn → ADR.
- **MVP chỉ nạp tài liệu số** (native PDF/DOCX/Excel) — OCR bảng scan descope ([ADR-0009](adr/0009-local-model-stack.md)).

---

## PHASE 0 — Nền tảng repo & bộ khung (đang thực thi)
**Mục tiêu:** codebase boot được, cấu trúc module rõ, hạ tầng dev chạy.
- [ ] `pyproject.toml` (deps: fastapi, sqlalchemy[asyncio], asyncpg, pgvector, pydantic-settings, docling, sentence-transformers, rank-bm25, httpx, python-jose, arq/redis).
- [ ] Cấu trúc `app/` modular monolith (config, database, security, ingestion, rag, data_layer, llm, agent, erp, api).
- [ ] `app/config.py` — Pydantic Settings (DB, LLM endpoint, pepper, cloud on/off).
- [ ] `app/database/` — async engine/session + ORM models (Employee, Department, EmployeeDepartment, Source, Chunk, Draft, AuditLog).
- [ ] `app/main.py` — FastAPI app + lifespan + router wiring.
- [ ] `docker-compose.yml` — postgres+pgvector, redis, app, worker, (vllm/ollama placeholder).
- [x] `.env.example`, `alembic/` (env.py + migration `0001_init`: extension + tables + FTS/HNSW/GIN index), `tests/` (RLS unit test), `README-DEV.md`.
- **Cổng ra:** `docker compose up` → API `/health` trả 200. ✅ *(code đã xong; cần `pip install` + Postgres để chạy thật.)*

## PHASE 1 — MVP: Cổng tri thức & RLS
### 1A. Bảo mật & RLS (vương miện — viết lại từ pattern arkon)
- [ ] `app/security/rls.py` — `build_document_filter()`, `can_access(identity, resource)`; lọc scope **trong SQL** (predicate pushdown).
- [ ] `app/security/auth.py` — JWT, `Identity` (employee + department_ids + permissions), `require_permission()`.
- [ ] Token hash HMAC+pepper; out-of-scope hint (chỉ loại+số lượng).
- [ ] Audit log mọi truy cập đặc quyền.
- [ ] `/rls-check` xanh cho mọi endpoint.

### 1B. Ingestion (chuyển thể docsgpt) + provenance
- [x] `app/ingestion/parser.py` + **`pdf_parser.py` (pypdf)** — dispatch: PDF→pypdf (tiếng Việt sạch, page provenance, **đã test trên corpus BRAVO 10 thật**), khác→Docling (optional). **No OCR** (screenshot bỏ qua).
- [x] **Corpus MVP = 19 chương cẩm nang BRAVO 10** (`UserGuide_B10_TV_PDF/`, scope global) — script `scripts/ingest_userguide.py`. *(Scope KB hiện chốt ở đây; mở rộng sau khi có kết quả tốt.)*
- [x] Provenance `page_number`/`heading_path`/`is_table` gắn vào `ParsedBlock` (trong parser — khoảng trống docsgpt đã lấp). *(sheet/cell XLSX còn TODO.)*
- [x] `app/ingestion/chunker.py` — heading-aligned, tách bảng riêng.
- [x] `app/ingestion/pipeline.py` — embed (bge-m3) → pgvector. *(resumable = TODO.)*
- [x] Gắn `department_ids`/scope cho mỗi chunk lúc nạp.

### 1C. RAG có trích dẫn
- [x] `app/rag/embedding.py` — bge-m3 cục bộ.
- [x] `app/rag/retriever.py` — **RLS-on-vector** (scope trong query) + **hybrid BM25(FTS)+vector+RRF** + **rerank** (`rag/rerank.py` ViRanker).
- [x] Trả lời kèm trích dẫn (nguồn + trang/ô) + cơ chế **từ chối** khi thiếu căn cứ (`api/routes_ask.py`).
- [x] `app/llm/router.py` — Model Router (local Qwen2.5 mặc định; cloud opt-in fail-closed).

### 1D. Giao diện & MCP
- [x] API hỏi-đáp (`/api/ask`) + nguồn + `/api/me` + upload/list sources.
- [x] MCP server scoped-by-token (`app/mcp/server.py`, `kb_search`).
- [x] Frontend tối thiểu (`frontend/` — login + ask + citations, static, no build).

### 1E. Eval (cổng ra chất lượng)
- [x] Khung golden Q&A (`app/eval/golden.py`) + golden_set.example.yaml; runner `app/eval/run.py` (gate ≥95% + 0 leak).
- [x] **Probe rò chéo ACL** (`app/eval/probes.py`) — bắt lớp lỗi Slack/Sage; release blocker nếu rò.
- [ ] RAGAS/DeepEval faithfulness (generator) + benchmark masked-span tiếng Việt.
- **Cổng ra Phase 1:** citation accuracy ≥95%; 0 rò scope (probe ACL); pilot 1 phòng ban.

## PHASE 2 — Agent & ERP read
- [x] `app/agent/memory.py` — **MemoryStore** core/recall/archival trên pgvector, archival **RLS-scoped** (pattern letta, không full Letta).
- [x] `app/agent/tools.py` — tool registry; read(auto)/write(`requires_approval`) + `payload_hash`.
- [x] `app/erp/draft_queue.py` + `routes_drafts.py` — **luồng draft→duyệt (HITL)**: tạo nháp (hash pinned) → list pending → approve (verify hash anti-drift) → reject; audit đầy đủ. *(Push sang ERP staging = chờ YC#3.)*
- [x] `app/data_layer/semantic.py` — metric registry + execute deterministic + **abstain** ngoài registry (test PASS). *(LLM plan_fn + DataSource ERP thật = chờ API BRAVO.)*
- [x] `app/data_layer/calc.py` — **sandbox AST an toàn** (no import/attr/call ngoài whitelist); LLM không xuất số cuối (test PASS).
- [x] `app/data_layer/grounding.py` — **verify gate**: parse số tiếng Việt (khử nhập nhằng bằng giá trị engine) + bắt số bịa (test PASS).
- [x] `app/agent/loop.py` — **agent loop**: ráp core/recall memory + retrieval RLS + Model Router + draft (write→nháp). *(Tool-calling protocol của model = tích hợp tiếp.)*
- [ ] `app/erp/client.py` + DataSource ERP thật + danh mục metric đã duyệt — **CHỜ: API read-only của BRAVO ERP + danh mục view/metric (VISION §8).**
- [ ] `app/erp/client.py` — ERP read-only REST (qua view/metric đã duyệt).
- **Cổng ra:** độ chính xác số liệu eval đạt ngưỡng; kế toán xác nhận tin dùng.

## PHASE 3 — Phân tích chủ động & Draft automation
- [ ] Phát hiện bất thường (agent nền theo lịch, cảnh báo có dẫn chứng).
- [ ] `app/erp/draft_queue.py` — soạn nháp chứng từ/định khoản → hàng đợi ERP (advisory-lock duyệt).
- [ ] Báo cáo quản trị NL.
- [ ] Roadmap **Thông tư 99/2025** (hệ tài khoản mới).

## PHASE 4 — Đóng gói thương mại
- [ ] Helm chart / installer air-gapped; cấu hình theo khách tách khỏi code.
- [ ] Định giá (per-site/module, minh bạch); demo "đinh"; tài liệu bán.

---
## Trạng thái tổng
| Phase | Trạng thái |
|-------|-----------|
| 0 — Nền tảng | ✅ Xong (code) |
| 1 — MVP tri thức | ✅ Xong (code) — 1A RLS · 1B ingestion · 1C RAG hybrid · 1D API+MCP+frontend · 1E eval+ACL probe. *(RAGAS faithfulness: hook sẵn, cần cấu hình judge local. Chạy thật cần pip+Postgres+LLM.)* |
| 2 — Agent + ERP | 🔄 **Non-ERP XONG**: data layer (calc+semantic+grounding, catalog 18 metric) · agent (memory+tools+loop) · draft/HITL. **Chờ BRAVO**: API read-only + mapping metric → DataSource thật. |
| 3 — Chủ động + draft | ⏳ |
| 4 — Thương mại | ⏳ |
