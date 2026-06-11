# WP-A — Ingestion Docling + provenance (page/sheet/cell) + corpus Demo A

> Module: `app/ingestion`. **Đọc [CONTRACTS.md](CONTRACTS.md) trước.** Phụ thuộc: không.

## Mục tiêu
Bóc tài liệu **không làm vỡ bảng tài chính** và **gắn provenance đủ để trích dẫn tới ô** (invariant #3). Nạp corpus Demo A (file trong `file_system/`, gồm `.docx`).

## Reuse (ADR-0013) — đừng tái tạo bánh xe
- **Docling là dep CHÍNH** (gỡ khỏi optional trong [pyproject.toml](../../pyproject.toml)). Dùng `DocumentConverter` với `do_table_structure=True`, `do_ocr=False`.
- **Provenance ô/sheet bóc từ Docling** `TableItem.prov` — KHÔNG tự tính toạ độ ô bằng openpyxl (lệch = citation sai = số sai).
- Lớp `ParsedBlock` (page/sheet/cell/heading) là **glue BRAVO** — giữ tự viết (đã có khung [parser.py:20-28]).

## Scope IN / OUT
**IN:** dispatch parser theo **loại tài liệu / có-bảng-hay-không** (KHÔNG theo đuôi file); Docling cho PDF-có-bảng + DOCX + XLSX; pypdf **fast-path** cho PDF **text-thuần** (user-guide BRAVO 10 — pypdf bóc tiếng Việt sạch hơn); điền `sheet_name`/`cell_range` (đóng TODO [parser.py:93]); pin version Docling + test parse trong CI; quy trình bake model Docling offline (ghi doc, không cần chạy ở demo cloud).
**OUT (đừng làm):** OCR full-page (`do_ocr=False` — descope OCR scan, [ADR-0009]); vendor/fork code docsgpt; tự viết table-structure; parser cho định dạng ngoài PDF/DOCX/XLSX.

## Files
`app/ingestion/parser.py` (dispatch + ParsedBlock) · `pdf_parser.py` (giữ pypdf fast-path) · `pipeline.py` (thêm nhánh xlsx) · `chunker.py` (giữ table-whole) · `pyproject.toml` (Docling→chính) · `scripts/ingest_userguide.py` (mở rộng nạp `file_system/`).

## Việc cụ thể
1. `parser.py`: hàm `detect_kind(path) -> {"pdf_text","pdf_table","docx","xlsx"}` (PDF: thử phát hiện bảng; nếu có → Docling). Mọi nhánh trả `list[ParsedBlock]` với `page_number|sheet_name|cell_range|heading_path|is_table`.
2. PDF-có-bảng/DOCX/XLSX → Docling; map `TableItem` → ParsedBlock giữ nguyên ô; `is_table=True` (chunker không split).
3. PDF text-thuần → giữ pypdf (page provenance).
4. Nạp corpus Demo A: `Tài liệu bravo 10 cho khối kỹ thuật.docx`, `UserGuide_B10_Basic rules.pdf`, `BRAVO_BI_Guidelines_Full.pdf` + 19 chương → scope global (không nhạy).

## Acceptance (test)
- PDF có bảng số → ô KHÔNG bị làm phẳng (giữ hàng/cột); 1 ô có `cell_range` không None.
- `.docx` nạp được (pypdf không đọc được .docx — phải qua Docling).
- XLSX: 1 số trích dẫn được tới `sheet_name`+`cell_range`.
- User-guide PDF text-thuần vẫn ra tiếng Việt sạch + `page_number`.
- CI: test parse 1 file mẫu mỗi loại (pin Docling version).

## Invariant
#3 (provenance để citation kiểm chứng — đặc biệt bảng/Excel kế toán).

## Phụ thuộc
Không. (Cung cấp ParsedBlock cho pipeline embed sẵn có.)
