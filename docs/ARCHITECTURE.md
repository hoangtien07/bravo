# ARCHITECTURE — BRAVO AI Copilot

> Kiến trúc tổng hợp từ arkon + docsgpt + letta. Mọi lựa chọn cụ thể (vector store, model, ...) chốt qua [adr/](adr/). Mục tiêu & ràng buộc: [VISION.md](VISION.md).

> ⚠️ **Trạng thái (cập nhật 2026-06):** phần lõi đã có code + test (RAG+RLS, agent loop, verify-gate, money-engine AP parser, chat SSE) **chạy trên dữ liệu MOCK**. Phần **tích hợp ERP** (client đọc, đẩy nháp→staging) còn là **stub** ([erp/client.py](../app/erp/client.py), [draft_queue.py:107](../app/erp/draft_queue.py#L107)) — chờ BRAVO mở REST API ([ERP-INTEGRATION-REQUEST.md](ERP-INTEGRATION-REQUEST.md)). Một số đoạn dưới đây mô tả đích nhắm, chưa hẳn = code hiện tại; chỗ nào còn là đề xuất sẽ ghi rõ.

## 1. Sơ đồ khối tổng quan

```
                         ┌───────────────────────────────────────────────┐
                         │                NGƯỜI DÙNG                       │
                         │   Web UI (Next.js)   ·   MCP (Claude Desktop)   │
                         └───────────────┬───────────────────────────────┘
                                         │  (đã xác thực, mang identity + scope)
                         ┌───────────────▼───────────────┐
                         │        API GATEWAY (FastAPI)   │
                         │   AuthN/AuthZ · require_perm   │  ◄── RLS bắt đầu ở đây
                         └───────┬───────────────┬────────┘
                                 │               │
                ┌────────────────▼───┐     ┌─────▼─────────────────┐
                │   AGENT CORE        │     │   KNOWLEDGE / RAG      │
                │   (mượn từ letta)   │     │   (mượn từ docsgpt)    │
                │  · core/archival/   │     │  · retriever + rerank │
                │    recall memory    │     │  · scope-filtered      │
                │  · tool-calling     │     │    vector search       │
                │  · requires_approval│     └─────┬─────────────────┘
                └───┬─────────────┬───┘           │
                    │             │               │
        ┌───────────▼──┐   ┌──────▼───────┐  ┌────▼───────────────┐
        │ ERP TOOLS    │   │ KB TOOLS     │  │  INGESTION         │
        │ (READ-ONLY)  │   │ (search/read │  │  (docsgpt/Docling) │
        │ REST → BRAVO │   │  cited)      │  │  PDF/DOCX/XLSX →    │
        │ ERP API      │   └──────────────┘  │  bảng + provenance │
        └──────┬───────┘                     └────┬───────────────┘
               │  (chỉ đọc)                        │
        ┌──────▼───────┐                    ┌──────▼───────────────────────┐
        │ DRAFT QUEUE  │  (ghi = nháp)      │  STORE                        │
        │ → giao diện  │                    │  Postgres + pgvector ·        │
        │   ERP duyệt  │                    │  object storage (MinIO/đĩa)   │
        └──────────────┘                    └───────────────────────────────┘

   MODEL ROUTER → [LLM cục bộ Qwen-2.5 (mặc định)]  +  [cloud opt-in, chỉ dữ liệu được phép]  ·  Embedding cục bộ
   Sàn offline luôn đảm bảo · dữ liệu nhạy ghim cứng trong mạng nội bộ
```

## 2. Các tầng & nguồn gốc pattern

### 2.1 Tầng truy cập (Access) — *nguồn: arkon*
- **FastAPI** + async SQLAlchemy. Mỗi request mang `identity` (employee + department_ids + permissions).
- `require_permission("resource:action")` ở route; **scope filter dựng trong SQL** trước khi truy vấn (`build_*_filter`).
- **MCP server (FastMCP)** cho tích hợp Claude/Copilot ngoài; token hash HMAC+pepper, mỗi tool tự `apply_scope_filter`.

### 2.2 Tầng tri thức / RAG — *nguồn: docsgpt + arkon*
- **Ingestion (docsgpt/Docling):** PDF/DOCX/PPTX/XLSX → text + **bảng giữ cấu trúc** + OCR lai. **Mở rộng metadata** mỗi chunk: `page_number`, `sheet_name`, `cell_range`, `table_id`, `heading_path`, `department_id/scope`.
- **Chunking:** heading-aligned, token-based; bảng tách chunk riêng.
- **Embedding cục bộ (bge-m3 — [ADR-0009](adr/0009-local-model-stack.md))** → **pgvector**.
- **Retrieval (bộ công cụ đã nghiên cứu — [findings/J](research/findings/J-rag-agent-eval.md)):**
  - **RLS-on-vector:** điều kiện scope ghép **ngay trong truy vấn** (predicate pushdown trên pgvector) — *KHÔNG lọc post-retrieval* (lọc sau sụp recall 1.000→0.002 ở 50k tài liệu; lọc trong query = 0% rò). Học thuật ủng hộ trực tiếp.
  - **Hybrid BM25 + vector + RRF** (BM25 vượt dense trên tài liệu tài chính — bắt mã chứng từ/số/tên riêng).
  - **Reranking** (đòn bẩy chất lượng #1: −67% thất bại / +17đ): top-150 → rerank (ViRanker/Cohere) → top-20.
  - (Tuỳ chọn) **Contextual Retrieval** (Anthropic — gain nhất quán, rẻ với prompt caching).
- **Biên soạn có kiểm chứng (arkon MRP):** với tri thức quan trọng, biên soạn trước thành trang có trích dẫn `[^N]` + bước **Verify** đối chiếu nguồn. Hỏi-đáp nhanh thì RAG trực tiếp.

### 2.3 Tầng agent — *nguồn: letta*
- **Bộ nhớ ba tầng:** core (ngữ cảnh người dùng/phiên, nằm trong context), archival (kiến thức/tóm tắt lâu dài, vector-searchable), recall (lịch sử hội thoại).
- **Tool-calling:** agent gọi *KB tools* (search/read có trích dẫn) và *ERP tools* (REST read-only). Mỗi tool tự áp scope.
- **`requires_approval`:** tool ghi không thực thi trực tiếp — sinh **draft** vào hàng đợi.
- **Quản lý context window:** đếm token, tóm tắt khi áp lực context (letta pattern) — quan trọng vì LLM cục bộ có context giới hạn.

### 2.4 Tầng tích hợp ERP — *mới, BRAVO xây*
- **Semantic Layer (bắt buộc, [ADR-0005](adr/0005-no-free-form-sql.md)):** agent **không sinh SQL tự do**. Mọi truy cập số liệu qua một danh mục **metric/view tham số hoá đã được kế toán duyệt & kiểm thử** (vd `doanh_thu_thuan(kỳ, đơn_vị)`). Đây cũng là điểm nhúng RLS (lọc scope ở SQL) và bảo đảm ngữ nghĩa kế toán (kỳ khoá sổ, đơn vị, nợ/có). *(Lý do: text-to-SQL tự do chỉ đạt ~21% trên ERP thật — [findings/C](research/findings/C-deployment-pitfalls.md).)*
- **Calculation Layer deterministic ([ADR-0004](adr/0004-llm-never-computes-numbers.md)):** mọi con số do truy vấn/biểu thức xác định tính ra — **LLM không tự tính**. LLM chỉ chọn metric + tham số, rồi diễn giải + trích dẫn kết quả. Có **cơ chế từ chối** khi không đủ dữ liệu (thay vì bịa).
- **ERP Read Client:** wrapper REST API một chiều tới BRAVO ERP; chỉ gọi view/API đã duyệt (qua Semantic Layer).
- **Draft Writer:** không ghi ERP; tạo bản ghi nháp (định khoản/chứng từ) → **Draft Queue** → giao diện ERP để người duyệt. Học workflow duyệt + advisory-lock từ arkon.

### 2.5 Tầng hạ tầng — *nguồn: cả ba + on-prem*
- **Postgres + pgvector** (dữ liệu + vector, ACID, hợp air-gapped). **Object storage** (MinIO/đĩa). **Redis/queue** cho worker nạp tài liệu (resumable như docsgpt). **Docker Compose / Helm**.

### 2.6 Model Router (LLM Gateway) — *hybrid, [ADR-0003](adr/0003-hybrid-llm-strategy.md)*
- **Mọi** lời gọi LLM của agent/RAG đi qua một router duy nhất — không thành phần nào gọi thẳng model.
- Router chọn backend theo: cấu hình (cloud bật/tắt, mặc định TẮT; nhà cung cấp cho phép) + **độ nhạy ngữ cảnh** (tính từ nhãn nguồn dữ liệu, tái dùng RLS) + loại tác vụ.
- **Mặc định & sàn:** LLM cục bộ Qwen-2.5 qua vLLM (GPU) / Ollama·llama.cpp (CPU/GGUF). **Cloud:** opt-in, chỉ cho lớp dữ liệu whitelist; dữ liệu nhạy ghim cứng local.
- **Fail-closed** (không rõ độ nhạy ⇒ local) + **audit egress**. Tận dụng abstraction OpenAI-compatible của docsgpt để cùng interface chạy local/cloud. Chính sách chi tiết: [SECURITY-RLS.md §9](SECURITY-RLS.md).

### 2.7 Tầng số liệu — *cốt lõi [ADR-0004](adr/0004-llm-never-computes-numbers.md)/[0005](adr/0005-no-free-form-sql.md), [findings/H](research/findings/H-data-layer-techniques.md)*
Nguyên tắc: **LLM CHỌN, engine TÍNH**. Luồng:
```
Câu hỏi → [Planner LLM — chỉ CHỌN] phân loại:
  (A) câu hỏi metric → SEMANTIC LAYER (Cube/MetricFlow): LLM map → (metric,dimension,filter,kỳ);
       engine sinh SQL deterministic, fan-out-safe, EXPLAIN-validate
  (B) câu hỏi trên bảng tài liệu → TABLE-RAG: parse giữ cấu trúc + provenance(trang/ô) → DuckDB
       → schema+cell retrieval → giải bằng SQL
  (C) ngoài phạm vi / thiếu dữ liệu → ABSTAIN (từ chối, không bịa)
        ↓ (phép phái sinh: YoY, tỷ lệ...)
  [CALC LAYER — sandbox không quyền ghi] PoT/PAL; số cuối từ interpreter, KHÔNG từ LLM
        ↓
  [GROUNDING & VERIFY GATE] mọi số gắn provenance · đối chiếu output engine · confidence<ngưỡng → mask/abstain
        ↓  Trả lời + trích dẫn tới metric def / ô nguồn
```
- **Semantic layer** loại được join/aggregation sai + bất nhất giữa các lần chạy (dbt 2026: ~100% trong phạm vi; *"báo không trả lời được, không bao giờ trả số sai"*). **Cube** ưu tiên (MCP + đã dùng cho finance ở Brex).
- **Abstention làm ở TẦNG HỆ THỐNG** — không dựa model tự biết dừng (reasoning fine-tuning *giảm* abstention 24%).
- **NL2SQL tự do bị KHÓA khỏi số liệu tài chính** (enterprise SOTA chỉ ~36% EX).

## 3. Luồng dữ liệu chính

**Hỏi tri thức:** câu hỏi → (rephrase) → vector search *đã lọc scope* → top-k chunks (kèm provenance) → LLM cục bộ tạo câu trả lời + trích dẫn `[nguồn, trang]` → (verify nếu bật) → trả về.

**Hỏi số liệu ERP:** câu hỏi → agent **chọn metric trong Semantic Layer + điền tham số** (không sinh SQL) → Calculation Layer tính deterministic (lọc scope/đơn vị/kỳ ở SQL) → số liệu chính xác + bản ghi nguồn → LLM **chỉ diễn giải + trích dẫn** + drill-down + nhãn "cần xác nhận" → trả về. *(Nếu không có metric phù hợp hoặc thiếu dữ liệu → từ chối, không bịa.)*

**Đề xuất ghi:** agent dựng bản ghi nháp (cân nợ-có, đủ trường) → `requires_approval` → Draft Queue → người duyệt trên ERP → ERP (không phải AI) thực hạch toán.

## 4. Ranh giới tin cậy (trust boundaries)
1. **Người dùng ↔ Gateway:** xác thực, gắn identity+scope. RLS bắt đầu.
2. **Gateway ↔ Store:** mọi query mang scope filter trong SQL.
3. **Copilot ↔ ERP:** một chiều, read-only; chiều ghi chỉ qua Draft Queue.
4. **Hệ thống ↔ Internet:** **đóng mặc định** (air-gapped). Chỉ mở có kiểm soát qua **Model Router** khi khách bật cloud, và chỉ cho lớp dữ liệu được whitelist — dữ liệu nhạy không bao giờ qua biên này (xem §2.6, [SECURITY-RLS §9](SECURITY-RLS.md)).

## 5. Điều cố ý chưa quyết (chờ ADR)
**Đã chốt:** hybrid LLM ([ADR-0003](adr/0003-hybrid-llm-strategy.md)) · LLM không tính số ([ADR-0004](adr/0004-llm-never-computes-numbers.md)) · không SQL tự do/semantic layer ([ADR-0005](adr/0005-no-free-form-sql.md)) · chiến lược code greenfield modular-monolith ([ADR-0007](adr/0007-code-strategy.md)) · model Qwen2.5-32B+bge-m3+VietOCR ([ADR-0009](adr/0009-local-model-stack.md)) · rerank=có, hybrid=có, RLS-on-vector ([findings/J](research/findings/J-rag-agent-eval.md)).
**Còn mở:**
- Vector store: pgvector (mặc định) vs Qdrant/Milvus cho quy mô lớn (cả 3 đều hỗ trợ predicate-pushdown cho RLS-on-vector).
- Semantic layer: Cube vs dbt MetricFlow (findings/H nghiêng Cube).
- Mức dùng MRP (biên soạn) vs RAG trực tiếp cho từng loại nội dung.
- Cơ chế đồng bộ phòng ban/quyền với ERP vs tự quản trị; danh mục view/metric đọc được duyệt.
- vLLM vs Ollama; danh sách nhà cung cấp cloud; lược đồ phân loại độ nhạy & policy egress; redaction PII.
- ⏸️ OCR bảng tài chính scan: **tạm descope khỏi MVP** (2026-06-09) — MVP chỉ nạp tài liệu số (native PDF/DOCX/Excel) qua Docling.

## 6. Bản đồ "mượn từ đâu" (truy vết kiến trúc)
| Thành phần BRAVO | Học từ | File tham chiếu |
|------------------|--------|-----------------|
| RLS filter ở SQL | arkon | `../arkon/app/services/permission_engine.py` |
| MCP scoped token | arkon | `../arkon/app/services/mcp_auth_service.py` |
| Workflow nháp→duyệt | arkon | `../arkon/app/routers/wiki_drafts.py` |
| Pipeline trích dẫn | arkon | `../arkon/app/ai/mrp/` |
| Parse PDF/Office/bảng | docsgpt | `../docsgpt/application/parser/file/docling_parser.py` |
| Chunking | docsgpt | `../docsgpt/application/parser/chunking.py` |
| LLM/vector abstraction | docsgpt | `../docsgpt/application/llm/`, `vectorstore/` |
| Ingest resumable | docsgpt | `../docsgpt/application/parser/embedding_pipeline.py` |
| Bộ nhớ agent | letta | `../letta/letta/schemas/memory.py` |
| Tool-calling + sandbox | letta | `../letta/letta/services/tool_executor/` |
| requires_approval | letta | `../letta/letta/schemas/tool.py` |
| LLM cục bộ vLLM | letta | `../letta/docker-compose-vllm.yaml` |
