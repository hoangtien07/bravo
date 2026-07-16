# BRAVO AI Continuation Notes

> **Status: ARCHIVED SUPERSEDED SNAPSHOT.** This corpus-cleanup checkpoint no longer owns current
> project progress. See [PROJECT-STATE.md](../../PROJECT-STATE.md). The archive decision is recorded
> in [MARKDOWN-CLEANUP-ACTIONS.md](../../documentation/MARKDOWN-CLEANUP-ACTIONS.md).

> Checkpoint hiện tại sau khi rà lại nguy cơ over-engineering của mindmap kỹ thuật.

## Cơ chế tìm tài liệu hiện tại

Dự án đang dùng RAG trên Postgres/pgvector:

- `Source`: lưu file nguồn và `knowledge_type` để hiển thị/citation.
- `Chunk`: lưu `content`, `embedding` dạng `pgvector`, provenance `page_number/sheet_name/cell_range/heading_path`, và `extra` dạng JSONB.
- `Chunk.extra`: chứa metadata từ manifest như `source_type`, `module`, `business_area`, `lifecycle_stage`, `audience`, `source_path`.
- Retrieval hiện tại:
  - dense vector search bằng `Chunk.embedding.cosine_distance`;
  - lexical search bằng Postgres full-text search;
  - RRF fuse;
  - optional rerank;
  - BRAVO intent boost theo metadata `source_type/module/lifecycle_stage`.

Metadata hiện dùng để boost/eval sau retrieval, chưa phải graph/mindmap engine riêng.

## Quyết định về mindmap

Giữ:

- 19 mindmap phân hệ gốc trong `file_system/Mindmaps/`.
- Lý do: nhỏ, giúp định tuyến/tóm tắt nghiệp vụ phân hệ, nhất là câu hỏi kiểu "luồng/quy trình/chức năng nằm ở đâu".

Dọn khỏi active corpus:

- `Mindmap_TechnicalArchitecture.md` do agent tự tổng hợp.
- 11 mindmap kỹ thuật chi tiết copy từ `D:\02.DaoTaoNoiBo\Bravo10\TaiLieuKyThuat_Dll`.

Lý do dọn:

- Nội dung kỹ thuật đã có trong `TaiLieuBravo10_KhoiKyThuat.docx` và 11 PDF `TaiLieuKyThuat_Dll`.
- Mindmap kỹ thuật là nguồn derived/summary, dễ trùng nội dung và có thể làm citation kém chắc hơn tài liệu gốc.
- Chưa có eval chứng minh chúng cải thiện retrieval/answer quality.
- Thêm nguồn làm tăng chunk/embedding và có nguy cơ over-engineering.

## Trạng thái corpus sau cleanup

- Manifest hiện có `72` sources.
- Mindmap active: `19` file phân hệ.
- Mindmap kỹ thuật active: `0`.
- Tài liệu kỹ thuật gốc vẫn giữ:
  - `TaiLieuBravo10_KhoiKyThuat.docx`.
  - 11 PDF trong `file_system/TaiLieuKyThuat_Dll/`.

## Việc nên làm tiếp

1. Không nạp thêm derived mindmap nếu chưa có eval chứng minh lợi ích.
2. Nếu cần cải thiện câu hỏi kỹ thuật, ưu tiên:
   - metadata chi tiết hơn trong manifest/source extra;
   - chunking tốt hơn theo heading;
   - eval retrieval cho `Datasource`, `Editor`, `Explorer`, `Reporter`, `Dashboard`;
   - query routing/boost dựa trên `source_type=technical_manual`, `module`, `lifecycle_stage`.
3. Chỉ đưa mindmap kỹ thuật trở lại nếu A/B eval cho thấy cải thiện rõ recall/precision hoặc giảm hallucination.

## Lệnh kiểm chứng

```powershell
& 'C:\Users\tienph\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 -m app.eval.bravo_readiness
```

```powershell
& 'C:\Users\tienph\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m compileall app/rag/bravo_intent.py app/ingestion/manifest.py app/eval/bravo_readiness.py tests/test_bravo_intent.py tests/test_bravo_corpus_manifest.py
```
