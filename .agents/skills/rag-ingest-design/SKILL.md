---
name: rag-ingest-design
description: "Thiết kế hoặc đánh giá luồng nạp (ingestion) cho một loại tài liệu mới — PDF/DOCX/Excel/scan — với trọng tâm bóc tách bảng biểu, truy vết số trang/ô, chunking, embedding offline, và trích dẫn kiểm chứng được. Triggers: ingest design, thiết kế nạp tài liệu, parse pdf/excel, bóc tách bảng, ingestion pipeline, chunking, trích dẫn nguồn."
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
---

# rag-ingest-design: Thiết kế luồng nạp tài liệu

Mục tiêu: với một loại tài liệu, thiết kế luồng **parse → bóc bảng → chunk → embed → lưu** sao cho giữ được cấu trúc bảng và truy vết được tới **số trang/sheet/ô** — nền tảng để trích dẫn không ảo tưởng.

## Tham chiếu (DocsGPT + Arkon)
- Parser đa định dạng: `../docsgpt/application/parser/file/docling_parser.py` (Docling, table_structure, OCR lai), `tabular_parser.py` (Excel/CSV qua pandas), `bulk.py` (chọn parser).
- Chunking: `../docsgpt/application/parser/chunking.py` (token-based, heading).
- Metadata/provenance: `../docsgpt/application/parser/schema/base.py` (Document.extra_info) — **lưu ý: docsgpt mặc định KHÔNG track số trang, phải mở rộng.**
- Biên soạn có trích dẫn: `../arkon/app/ai/mrp/` (source_outline, citations `[^N]`, verifier đối chiếu nguồn).

## Quy trình thiết kế

1. **Đặc tả tài liệu.** Định dạng? Có scan/ảnh (cần OCR)? Có bảng tài chính dày? Cấu trúc heading? Kích thước điển hình? Ngôn ngữ (tiếng Việt — kiểm tra OCR/tokenizer hỗ trợ)?

2. **Chiến lược parse.** Chọn parser (Docling cho PDF/Office). Quyết định OCR (lai theo vùng vs full-page). **Bảng biểu**: giữ cấu trúc thành markdown table; với Excel giữ tên sheet + dải ô. Đừng làm phẳng bảng thành text trơn — số liệu sẽ mất nghĩa.

3. **Provenance (bắt buộc).** Định nghĩa metadata mỗi chunk PHẢI mang: `source_id`, **page_number** (mở rộng từ Docling page bounds), `sheet_name`/`cell_range` (Excel), `heading_path`, `table_id` (nếu là bảng). Đây là khoảng trống docsgpt để lại — lấp ngay từ thiết kế.

4. **Chunking.** Heading-aligned, tôn trọng ranh giới bảng (không cắt bảng giữa chừng — tách bảng thành chunk riêng kèm header lặp lại). Kích thước phù hợp context của LLM cục bộ.

5. **Embedding offline.** Model embedding chạy cục bộ (sentence-transformers / model đa ngữ hỗ trợ tiếng Việt). Xác nhận số chiều khớp vector store (pgvector). Không gọi API cloud.

6. **Lưu + scope.** Mỗi chunk gắn `department_id`/scope ngay khi nạp (để RLS lọc ở SQL về sau — phối hợp `/rls-check`).

7. **Kiểm chứng trích dẫn.** Thiết kế bước verify: câu trả lời trích `[^N]` phải đối chiếu được về đúng chunk + trang. Thêm vào bộ eval: citation accuracy, table fidelity.

## Đầu ra
- Sơ đồ luồng nạp cho loại tài liệu này (các bước + công cụ).
- Bảng schema metadata chunk (trường + nguồn lấy).
- Danh sách rủi ro mất thông tin (bảng vỡ, OCR sai, mất số trang) + cách giảm thiểu.
- Gợi ý test/eval để đo chất lượng nạp.
