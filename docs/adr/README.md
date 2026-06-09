# Architecture Decision Records (ADR)

Mỗi ADR ghi lại **một** quyết định kiến trúc quan trọng tại thời điểm đưa ra: bối cảnh, các phương án, lựa chọn và hệ quả. ADR là *bất biến* sau khi `Accepted` — muốn đổi thì viết ADR mới thay thế.

Tạo ADR mới: dùng skill **`/adr-new`** (tự đánh số, theo mẫu, cập nhật index này).

## Index

| # | Tiêu đề | Trạng thái | Ngày |
|---|---------|-----------|------|
| [0001](0001-record-architecture-decisions.md) | Dùng ADR để ghi quyết định kiến trúc | Accepted | 2026-06-08 |
| [0002](0002-architecture-as-synthesis-of-three-repos.md) | Kiến trúc = tổng hợp pattern từ arkon + docsgpt + letta (mượn, không fork) | Accepted | 2026-06-08 |
| [0003](0003-hybrid-llm-strategy.md) | Chiến lược LLM Hybrid: local mặc định + cloud opt-in có kiểm soát theo độ nhạy | Accepted | 2026-06-08 |
| [0004](0004-llm-never-computes-numbers.md) | LLM không bao giờ tự tính số liệu — tầng tính toán deterministic | Accepted | 2026-06-08 |
| [0005](0005-no-free-form-sql.md) | Không sinh SQL tự do trên ERP — semantic layer / view kế toán đã duyệt | Accepted | 2026-06-08 |
| [0006](0006-market-positioning.md) | Định vị thị trường: "AI tài chính có chủ quyền & không bịa số" | Accepted | 2026-06-08 |
| [0007](0007-code-strategy.md) | Chiến lược code: lõi greenfield hợp nhất, modular-monolith; mượn pattern/chuyển thể | Accepted | 2026-06-08 |
| [0008](0008-arkon-license-ownership.md) | arkon = chỉ học pattern, **VIẾT LẠI** — không tái dùng code (gỡ rủi ro PolyForm) | Accepted | 2026-06-09 |
| [0009](0009-local-model-stack.md) | Bộ model cục bộ: Qwen2.5-32B + bge-m3 + VietOCR | Accepted | 2026-06-08 |

## Quyết định đang chờ (backlog — sẽ thành ADR khi chốt)
Tham chiếu [../ARCHITECTURE.md §5](../ARCHITECTURE.md) và [../VISION.md §8](../VISION.md):
- Vector store: pgvector vs Qdrant/Milvus.
- ~~Model LLM cục bộ~~ → **đã chốt [0009](0009-local-model-stack.md)** (Qwen2.5-32B + bge-m3 + VietOCR). Còn mở: vLLM vs Ollama; danh sách nhà cung cấp cloud.
- ~~Reranker cục bộ có/không~~ → **CÓ** (rerank là đòn bẩy chất lượng #1 — [findings/J](../research/findings/J-rag-agent-eval.md)); ViRanker/Cohere.
- Semantic layer: Cube vs dbt MetricFlow ([findings/H](../research/findings/H-data-layer-techniques.md) nghiêng Cube — MCP + finance).
- Lược đồ phân loại độ nhạy (sensitivity classification) & cơ chế cấu hình policy egress theo khách; có/không lớp redaction PII.
- Mức dùng pipeline biên soạn (MRP) vs RAG trực tiếp theo loại nội dung.
- Cơ chế tích hợp ERP: đồng bộ phòng ban/quyền với ERP vs tự quản trị; danh mục view/API đọc được duyệt.
- Reranker cục bộ: có/không.
