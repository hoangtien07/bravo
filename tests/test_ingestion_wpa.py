"""WP-A — Ingestion dispatch + provenance (page/sheet/cell) tests.

Covers the acceptance list in WP-A-ingestion-docling.md:
  - detect_kind dispatches by TYPE/has-table, not extension alone;
  - text-PDF user-guide goes through the pypdf fast-path -> clean Vietnamese + page_number
    (this test RUNS FOR REAL on a chapter PDF in file_system/);
  - PDF-with-tables / DOCX / XLSX go through Docling, tables kept cell-by-cell with
    page/sheet/cell provenance (these tests `importorskip('docling')` — skipped until the
    heavy dep is installed/baked offline).

Docling is a heavy dep (torch + models). It is NOT installed on the dev box, so the
Docling-dependent tests skip cleanly. The pypdf path is exercised against the real corpus.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.ingestion.parser import (
    ParsedBlock,
    _excel_cell,
    _line_is_tabular,
    detect_kind,
    parse,
)

_FS = Path(__file__).resolve().parents[1] / "file_system"
_PDF_DIR = _FS / "UserGuide_B10_TV_PDF"
# A representative text-clean Vietnamese chapter PDF (accounting).
_TEXT_PDF = _PDF_DIR / "NB_UserGuide_B10_Chapter17_Accounting.pdf"
_DOCX = _FS / "TaiLieuBravo10_KhoiKyThuat.docx"


# --- detect_kind dispatch (no Docling needed) -------------------------------------

def test_detect_kind_by_type_not_extension():
    assert detect_kind("foo.docx") == "docx"
    assert detect_kind("foo.md") == "markdown"
    assert detect_kind("foo.xlsx") == "xlsx"
    assert detect_kind("foo.xlsm") == "xlsx"


@pytest.mark.skipif(not _TEXT_PDF.exists(), reason="corpus PDF missing")
def test_detect_kind_textpdf_is_text_fastpath():
    # The BRAVO 10 chapter guides are prose -> pypdf fast-path, NOT Docling.
    assert detect_kind(_TEXT_PDF) == "pdf_text"


@pytest.mark.skipif(not _DOCX.exists(), reason="corpus DOCX missing")
def test_detect_kind_docx():
    assert detect_kind(_DOCX) == "docx"


def test_line_tabular_heuristic():
    # Aligned numeric rows (accounting table) -> tabular; prose -> not.
    assert _line_is_tabular("Doanh thu    1.200.000    2.400.000    3.600.000")
    assert _line_is_tabular("TK 111    50.000    60.000    70.000")
    assert not _line_is_tabular("Đây là một câu văn bình thường, không phải là bảng số")
    assert not _line_is_tabular("17.2 Các thiết lập hệ thống kế toán")


# --- pypdf fast-path: RUNS FOR REAL ------------------------------------------------

@pytest.mark.skipif(not _TEXT_PDF.exists(), reason="corpus PDF missing")
def test_pypdf_path_clean_vietnamese_and_page_number():
    blocks = parse(_TEXT_PDF)
    assert blocks, "expected at least one block from the chapter PDF"
    assert all(isinstance(b, ParsedBlock) for b in blocks)

    # Every text block carries a page_number (provenance) and none is a table.
    assert all(b.page_number is not None for b in blocks)
    assert all(not b.is_table for b in blocks)
    assert blocks[0].page_number == 1

    # Vietnamese diacritics survive extraction (pypdf, not OCR).
    sample = " ".join(b.text for b in blocks[:10])
    diacritics = sum(c in "ăâđêôơưàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụ" for c in sample.lower())
    assert diacritics > 50, "expected clean Vietnamese text from the user-guide PDF"


# --- Excel A1 cell address helper (no Docling needed) -----------------------------

def test_excel_cell_addressing():
    assert _excel_cell(0, 0) == "A1"
    assert _excel_cell(2, 3) == "D3"
    assert _excel_cell(0, 25) == "Z1"
    assert _excel_cell(0, 26) == "AA1"
    assert _excel_cell(9, 27) == "AB10"


def test_markdown_parse_preserves_heading_path(tmp_path):
    md = tmp_path / "Mindmap_Purchase.md"
    md.write_text(
        "# Purchase\n\n"
        "Overview text for purchase flow.\n\n"
        "## Purchase order\n\n"
        "- PO line 1\n"
        "- PO line 2\n",
        encoding="utf-8",
    )
    blocks = parse(md)
    assert [b.heading_path for b in blocks] == ["Purchase", "Purchase > Purchase order"]
    assert all(b.extra.get("format") == "markdown" for b in blocks)


# --- Docling path: SKIPPED until docling installed --------------------------------

def test_docx_needs_docling_runs_when_available():
    """DOCX must parse via Docling (pypdf cannot read .docx). Skips without docling."""
    pytest.importorskip("docling")
    if not _DOCX.exists():
        pytest.skip("corpus DOCX missing")
    blocks = parse(_DOCX)
    assert blocks, "Docling should yield blocks from the technical DOCX"
    assert all(isinstance(b, ParsedBlock) for b in blocks)


def test_pdf_with_tables_keeps_cells_when_docling_available():
    """A table-bearing PDF -> Docling; at least one table block with a cell_range.

    Acceptance: cells are NOT flattened (is_table True) and provenance is attached.
    Skips without docling, or if no table-PDF is present in the corpus.
    """
    pytest.importorskip("docling")
    # Find any PDF the heuristic routes to Docling.
    table_pdf = next(
        (p for p in sorted(_FS.rglob("*.pdf")) if detect_kind(p) == "pdf_table"), None
    )
    if table_pdf is None:
        pytest.skip("no table-bearing PDF in corpus to exercise Docling table path")
    blocks = parse(table_pdf)
    tables = [b for b in blocks if b.is_table]
    assert tables, "expected at least one table block from a table-bearing PDF"
    assert any(b.cell_range is not None for b in tables), "table should carry cell_range"


def test_xlsx_cell_and_sheet_provenance_when_docling_available():
    """XLSX: a table block cites sheet_name + cell_range. Skips without docling/fixture."""
    pytest.importorskip("docling")
    xlsx = next(iter(sorted(_FS.rglob("*.xlsx"))), None)
    if xlsx is None:
        pytest.skip("no XLSX fixture in corpus")
    blocks = parse(xlsx)
    tables = [b for b in blocks if b.is_table]
    assert tables, "expected table blocks from XLSX"
    cited = [b for b in tables if b.sheet_name and b.cell_range]
    assert cited, "at least one XLSX cell must be citable to sheet_name+cell_range"
