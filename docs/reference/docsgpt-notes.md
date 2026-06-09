# DocsGPT — Reference Notes

**Là gì:** RAG/documentation chatbot mã nguồn mở. **Vai trò với BRAVO:** lõi *ingestion & RAG offline* — đặc biệt parse đa định dạng + bóc tách bảng.

**Stack:** Flask + Flask-RESTX · Celery + Redis · PostgreSQL (+ MongoDB tuỳ chọn) · SQLAlchemy · React/Vite · OpenTelemetry.

---

## 1. Ingestion đa định dạng (Docling) ⭐⭐ — *điểm vàng*
- `application/parser/file/bulk.py` — `get_default_file_extractor()` chọn parser theo đuôi file; **mặc định Docling**.
- `application/parser/file/docling_parser.py`:
  - Hỗ trợ **PDF/DOCX/PPTX/XLSX/HTML/CSV/ảnh** (+ audio, markdown...).
  - **OCR lai (hybrid):** layout detection → text region trích thẳng (nhanh), bitmap region mới OCR (RapidOCR, không cần service ngoài). `force_full_page_ocr=False` mặc định.
  - **Table structure recognition:** `DoclingXLSXParser(table_structure=True, export_format="markdown")` → bảng giữ header/row/cell, xuất markdown table.

```python
pipeline_options = PdfPipelineOptions(do_ocr=..., do_table_structure=True)
```

- `application/parser/file/tabular_parser.py` — Excel/CSV qua pandas; `ExcelParser(header_period=20)` lặp header mỗi N dòng để giữ ngữ cảnh cho LLM.

**Lấy cho BRAVO:** dùng Docling làm parser chính. Bảng tài chính giữ cấu trúc là *bắt buộc*.

## 2. ⚠️ KHOẢNG TRỐNG: không track số trang
- Document schema (`application/parser/schema/base.py`) lưu metadata trong `extra_info` (filename, source, title) nhưng **mặc định KHÔNG có `page_number`**.
- **Hệ quả cho BRAVO:** lời hứa "trích dẫn kèm số trang" *không tự có* — phải **mở rộng**: trích page-bounds từ output Docling, thêm `page_number`, `sheet_name`, `cell_range`, `table_id`, `heading_path` vào metadata chunk. → skill `/rag-ingest-design`.

## 3. Chunking
- `application/parser/chunking.py` — `Chunker(chunking_strategy="classic_chunk", max_tokens, min_tokens)`; token-based (tiktoken); doc > max → tách, doc < min → giữ; giữ header ở chunk đầu, tuỳ chọn lặp header. Mặc định ~1250/150 tokens.

**Lấy cho BRAVO:** giữ heading; **tách bảng thành chunk riêng**, không cắt giữa bảng.

## 4. RAG retrieval
- `application/retriever/classic_rag.py` — `_rephrase_query()` (LLM condense theo lịch sử) → `docsearch.search(k)` đa nguồn → **token budget filter** → trả `{text, source, filename, title}`.
- Citation hiện ở mức **filename/source**, chưa tới trang (xem §2).

**Lấy cho BRAVO:** thêm **scope filter trong truy vấn** (docsgpt không có RLS — phải tự thêm, lấy từ arkon); nâng citation lên mức trang/ô.

## 5. Abstraction LLM & Vector — *cho offline* ⭐
- LLM: `application/llm/llm_creator.py` + `providers/` — 12+ provider. Quan trọng:
  - `providers/openai_compatible.py` → **Ollama / vLLM / LM Studio** qua `OPENAI_BASE_URL` (vd `http://localhost:11434`).
  - `llm/llama_cpp.py` → llama.cpp nạp `.gguf` cục bộ.
- Embedding (`vectorstore/base.py`): OpenAI / **HuggingFace sentence-transformers (cục bộ, không cần API)** / remote OpenAI-compatible.
- Vector store (`vectorstore/vector_creator.py`): **FAISS** (local, không cần server), MongoDB, **pgvector**, Qdrant, Elasticsearch, Milvus.

**Lấy cho BRAVO:** đường offline rõ ràng — llama.cpp/vLLM + HF embeddings + (BRAVO chọn) pgvector. Pattern abstraction này giúp đổi model/store dễ.

## 6. Ingest resumable (bài học vận hành)
- `application/parser/embedding_pipeline.py` — checkpoint theo chunk (`attempt_id`), resume sau lỗi; retry per-chunk (3 lần); flush partial khi fail.

**Lấy cho BRAVO:** nạp corpus lớn ở khách phải resumable — học pattern này.

## 7. Cấu trúc
`application/parser/` (file/, remote/, connectors/, chunking, embedding_pipeline) · `llm/` (+ providers/) · `vectorstore/` · `retriever/` · `api/` · `core/` (settings, model_registry, models/*.yaml) · `worker.py` (Celery) · `mcp_server.py`.

---
## ✅ Việc cần làm khác đi cho BRAVO
- **Thêm số trang/ô vào provenance** (khoảng trống lớn nhất).
- **Thêm RLS** — docsgpt không có phân quyền phòng ban; lấy từ arkon, áp trong truy vấn vector.
- Bộ eval **table-fidelity + citation accuracy** cho tài liệu kế toán tiếng Việt.
