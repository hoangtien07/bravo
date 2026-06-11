# FIX-REUSE-PLAN — sửa "worst of both worlds" (tái dùng thư viện proven thật sự)

> **Phê bình đang sửa (council):** bravo *vừa* tái tạo phiên bản mỏng *vừa* **CHƯA cài cả thư viện proven** (Docling, sentence-transformers) → nhận cái dở của cả hai; lớp glue invariant tự viết thì **chưa chứng minh ở runtime**.
> **Nguyên tắc sửa (phân biệt cho đúng — [ADR-0013](adr/0013-reuse-vs-rewrite-and-topology.md)):**
> - Phần **LIBRARY proven** (Docling, sentence-transformers/bge-m3, ViRanker, rank-bm25) → **CÀI + DÙNG THẬT** (đây là chỗ "đừng tái tạo bánh xe"). Lỗi hiện tại = khai trong deps nhưng chưa cài/chưa chạy.
> - Phần **glue mang invariant** (RLS-in-SQL, verify-gate, semantic, memory, loop) → council CHỐT **rewrite** vì coupling RLS; thay bằng letta/docsgpt sẽ **PHÁ RLS**. ⇒ KHÔNG thay; **HARDEN** để hết "mỏng = giòn".
> ⇒ Sửa = **dùng thư viện thật ở chỗ an toàn + làm cứng phần tự viết ở chỗ bắt buộc**, không phải bê app ngoài về.

---

## R1 — Cài thật các thư viện proven (đóng "vaporware gap")
**Vấn đề:** `.venv` dev thiếu `docling`, `sentence_transformers` (máy yếu, cài thủ công dở). Trên runtime Docker thì `pip install -e .` cài đủ.
**Việc:**
- `pip install -e .` (kéo docling, sentence-transformers, FlagEmbedding, rank-bm25, pydantic-ai-slim). Thêm `ViRanker` nếu `rag/rerank.py` dùng. **Pin version** (docling API 2.x version-sensitive).
- **Đây chính là điều xảy ra khi build image deploy** ([DEPLOY-DEMO.md](DEPLOY-DEMO.md)) → R1 hoàn tất "miễn phí" lúc deploy.
**Cổng ra:** trong image, `python -c "import docling, sentence_transformers, FlagEmbedding"` chạy; CI thêm 1 job cài-đủ-deps (không `importorskip`) chạy test ingestion thật.

## R2 — DÙNG Docling trên tài liệu THẬT (chứng minh bóc bảng — CRITICAL council)
**Vấn đề:** WP-A code dispatch Docling nhưng chưa từng chạy → bảng tài chính chưa được chứng minh giữ cấu trúc; `.docx` bạn thêm **chưa nạp được**.
**Việc:**
- Chạy `python -m scripts.ingest_userguide ./file_system` (đã sẵn) trong môi trường có Docling → nạp 19 chương (pypdf) **+ `.docx` + BI Guidelines (Docling)**.
- Thêm **1 tài liệu mẫu có BẢNG** (PDF/XLSX tài chính nhỏ) vào corpus → kiểm `do_table_structure=True` giữ ô + sinh `cell_range`/`sheet_name`.
**Cổng ra:** (a) hỏi nội dung trong `.docx` → có kết quả + trích dẫn; (b) hỏi một **số trong bảng** → trích dẫn tới **ô/sheet** (không phải "trang chung"); (c) bảng KHÔNG bị làm phẳng (so chunk `is_table=True`).

## R3 — Embedding LOCAL bge-m3 (bước chủ quyền THẬT, bỏ phụ thuộc embedding cloud)
**Vấn đề:** demo đang dùng cloud embedding (máy yếu) → mâu thuẫn pitch on-prem.
**Việc:** đặt `EMBEDDING_PROVIDER=local` + `EMBEDDING_MODEL=BAAI/bge-m3`; re-ingest. Trên VM deploy (8-16GB RAM) chạy được CPU.
**Cổng ra:** ingest + retrieval chạy với **0 egress embedding** (kiểm `AuditLog` không có call embedding cloud); chất lượng retrieval trên corpus thật đo bằng eval citation (≥ ngưỡng). ⇒ **một nửa sàn chủ quyền (embedding) đã THẬT**.

## R4 — HARDEN phần tự viết mỏng (KHÔNG thay bằng letta/docsgpt — sẽ phá RLS)
Đây là chỗ trả lời "mỏng = giòn" mà không phá invariant. Ưu tiên theo rủi ro:
1. **Context-window management** (memory.py TODO): evict ~70% + tóm tắt đệ quy khi context đầy → loop nhiều bước không vỡ trên model nhỏ. *(Mượn KHÁI NIỆM letta `context_window_calculator`, viết lại trên cấu trúc memory BRAVO.)*
2. **Resumable/idempotent ingestion** (mượn pattern docsgpt): nạp corpus lớn ngắt giữa chừng resume được (đã có Source.status; thêm checkpoint chunk).
3. **Error handling + retry** trong loop & router (model trả JSON hỏng, tool lỗi, cloud timeout) — hiện một số chỗ `except: pass` quá rộng, cần phân loại + log.
4. **Observability tối thiểu**: structured logging + (sau) OTel GenAI self-host → khi loop sai có trace, không "im lặng".
**Cổng ra:** hội thoại dài không vượt context (test); ingest resume sau ngắt; lỗi loop có log/trace; `except: pass` rộng được thu hẹp.

## R5 — Sàn LLM local (cái MOAT thật) — cần phần cứng, làm khi có
**Vấn đề:** chưa có model local nào chạy → moat chủ quyền vẫn ảo ở phần LLM.
**Việc:**
- **Ollama CPU (GGUF)** trên VM: `ollama run qwen2.5:7b-instruct` → trỏ `LLM_LOCAL_BASE_URL` vào Ollama → Model Router dùng local. Chậm nhưng **CHỨNG MINH air-gapped**.
- **Đo pass^k THẬT** (spike WS0 hoãn lâu nay): `python -m app.eval.run --passk` (nhánh real loop) trên Qwen local → ra con số độ tin cậy multi-turn (rủi ro #1 của nghiên cứu).
- Production: GPU (vLLM + Qwen2.5-32B-AWQ) — uncomment service trong `docker-compose.yml`.
**Cổng ra:** 1 câu trả lời bằng **Qwen local** (0 egress); **bảng pass^k thật** (14B/32B) → quyết định cỡ model + có cần LoRA. ⇒ **moat chủ quyền hết ảo**.

---

## Thứ tự & hội tụ với deploy
- **R1-R3 xảy ra NGAY khi deploy** ([DEPLOY-DEMO.md](DEPLOY-DEMO.md)): build image = R1; `bootstrap.sh` ingest = R2 + R3. ⇒ **deploy demo = đồng thời sửa phần lớn phê bình #6.**
- **R4** làm song song (độc lập, không cần VM).
- **R5** khi có VM đủ RAM/GPU — biến "demo cloud" thành "có đường local thật".

## Phê bình nào KHÔNG sửa bằng cách này (và vì sao)
- "Reimplement RLS/verify/memory/loop thay vì dùng arkon/letta" → **giữ nguyên rewrite** (ADR-0013: invariant coupling; arkon=PolyForm). Thay bằng code họ = **phá RLS tập trung** = vi phạm nguyên tắc #1. Đây là rewrite **đúng**, không phải "tái tạo bánh xe sai". Fix = **harden (R4)**, không phải thay.
- "0 user / chưa pilot" → không phải lỗi kỹ thuật; giải bằng **deploy demo → pilot** (quy trình), không phải sửa code.
