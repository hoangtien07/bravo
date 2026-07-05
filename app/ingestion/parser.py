"""Document parsing (Docling-based, derived from docsgpt MIT).

MVP: DIGITAL documents only (native PDF/DOCX/XLSX with text). NO OCR — scanned-table
OCR is descoped (ADR-0009, do_ocr=False). Tables are kept STRUCTURED, cell-by-cell — a
flattened table is meaningless for accounting numbers (rag-architect, invariant #3).

Each parsed block carries provenance (page/sheet/cell) so citations are verifiable —
this is the gap docsgpt left; we fill it here (WP-A).

DISPATCH is by document *kind* (type + has-table), NOT by file extension alone:
  - pdf_text   : digital PDF, no tabular layout -> pypdf fast-path (clean Vietnamese,
                 page provenance, proven on the BRAVO 10 corpus).
  - pdf_table  : digital PDF that LOOKS tabular (column-aligned numbers) -> Docling
                 (do_table_structure=True) so cells are not flattened.
  - docx/xlsx  : -> Docling (page/sheet/cell provenance from TableItem.prov).

NOTE: Docling's item-level API is version-sensitive. The mapping below targets Docling
2.x (`document.iterate_items()`, `*.prov[0]`, TextItem/TableItem/SectionHeaderItem) and
is guarded with getattr so it degrades gracefully; verify against the pinned version.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedBlock:
    text: str
    page_number: int | None = None
    sheet_name: str | None = None
    cell_range: str | None = None
    heading_path: str | None = None
    is_table: bool = False
    extra: dict = field(default_factory=dict)


# Kinds the dispatcher recognises (CONTRACTS §6 / WP-A item 1).
Kind = str  # one of: "pdf_text" | "pdf_table" | "docx" | "xlsx"


def detect_kind(path: str | Path) -> Kind:
    """Classify a document by *type and content*, not extension alone.

    .docx / .xlsx map straight to their kind (Docling). PDFs are probed: if a page
    looks tabular (many column-aligned, numeric rows) we route to Docling table
    extraction; otherwise the pypdf text fast-path. Probing is cheap (first few pages)
    and never raises — on any error we fall back to the safe text path.
    """
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        return "docx"
    if suffix in (".xlsx", ".xlsm"):
        return "xlsx"
    if suffix == ".pdf":
        return "pdf_table" if _pdf_has_tables(path) else "pdf_text"
    # Unknown extension: let Docling try (it sniffs the real format).
    return "pdf_text"


# A "tabular" line: >=3 runs of digits separated by >=2 spaces (column gutters) — the
# signature of an accounting table laid out in a digital PDF. Tuned to avoid matching
# prose (which has at most 1-2 such runs) and page footers.
_NUMCOL = re.compile(r"\d[\d.,]*")
_GUTTER = re.compile(r"\S {2,}\S")


def _line_is_tabular(line: str) -> bool:
    if _GUTTER.findall(line).__len__() < 2:
        return False
    return len(_NUMCOL.findall(line)) >= 3


def _pdf_has_tables(path: str | Path, *, probe_pages: int = 8, min_rows: int = 4) -> bool:
    """Heuristic: does the PDF contain a tabular block of accounting numbers?

    Reads up to `probe_pages` pages with pypdf (cheap, already a dep) and counts lines
    that look like aligned numeric rows. >= `min_rows` such lines on any page => route
    to Docling so the table is kept cell-by-cell. Pure read; never raises.
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        for page in reader.pages[:probe_pages]:
            text = page.extract_text() or ""
            tabular = sum(1 for ln in text.splitlines() if _line_is_tabular(ln))
            if tabular >= min_rows:
                return True
    except Exception:  # noqa: BLE001 — detection must never break ingestion
        return False
    return False


# --- Docling provenance helpers ---------------------------------------------------

def _page_of(item) -> int | None:
    prov = getattr(item, "prov", None)
    if prov:
        return getattr(prov[0], "page_no", None)
    return None


def _excel_cell(row: int, col: int) -> str:
    """0-based (row, col) -> Excel A1 address, e.g. (0,0)->'A1', (2,27)->'AB3'."""
    letters = ""
    c = col
    while True:
        letters = chr(ord("A") + c % 26) + letters
        c = c // 26 - 1
        if c < 0:
            break
    return f"{letters}{row + 1}"


def _table_cell_range(item) -> str | None:
    """A1 cell range cho một TableItem — CHỈ khi đọc được TOẠ ĐỘ THẬT của bảng trong sheet.

    Deep-dive (invariant #3): bản cũ neo cứng ở A1 (`A1:D{n}` từ num_rows/num_cols) bất kể
    bảng thật bắt đầu ở đâu -> citation trỏ tới ô SAI = số sai. Provenance ô phải lấy từ
    Docling TableItem.prov (toạ độ thật), KHÔNG tự tính. Hiện CHƯA pin Docling để đọc anchor
    thật -> trả None (citation tới sheet, không đoán ô) thay vì bịa.

    TODO(Docling pinned): map item.prov[0].bbox / cell absolute offset -> ô neo A1 thật,
    rồi mới phát hành cell_range. Có test trên fixture XLSX bảng KHÔNG bắt đầu ở A1.
    """
    start = getattr(item, "start_cell_a1", None)  # nếu version Docling phơi anchor thật
    end = getattr(item, "end_cell_a1", None)
    if start and end:
        return f"{start}:{end}"
    return None


def _sheet_name_of(item, doc) -> str | None:
    """Sheet name for an XLSX TableItem.

    Docling models each Excel sheet as a page; the page name (when present) is the
    sheet name. Try the item's prov page name first, then the doc's page registry.
    """
    prov = getattr(item, "prov", None)
    page_no = getattr(prov[0], "page_no", None) if prov else None
    pages = getattr(doc, "pages", None)
    if pages and page_no is not None:
        page = pages.get(page_no) if hasattr(pages, "get") else None
        name = getattr(page, "name", None) or getattr(page, "sheet_name", None)
        if name:
            return str(name)
    return None


def parse(path: str | Path) -> list[ParsedBlock]:
    """Parse a digital document into provenance-bearing blocks.

    Dispatch on detect_kind: pdf_text -> pypdf fast-path; pdf_table/docx/xlsx -> Docling
    (table structure on, OCR off). Every branch returns list[ParsedBlock].
    """
    kind = detect_kind(path)
    if kind == "pdf_text":
        from app.ingestion.pdf_parser import parse_pdf
        return parse_pdf(path)
    return _parse_docling(path, kind)


def _parse_docling(path: str | Path, kind: Kind) -> list[ParsedBlock]:
    """Docling path: PDF-with-tables, DOCX and XLSX.

    Tables become one ParsedBlock with is_table=True (chunker keeps them whole) carrying
    page/sheet/cell provenance straight from TableItem.prov — we do NOT recompute cell
    coordinates ourselves (CONTRACTS §6: lệch = citation sai = số sai).
    """
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    # do_table_structure=True keeps cells; do_ocr=False — no full-page OCR (ADR-0009).
    pdf_opts = PdfPipelineOptions(do_table_structure=True, do_ocr=False)
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts)}
    )
    result = converter.convert(str(path))
    doc = result.document

    blocks: list[ParsedBlock] = []
    heading_stack: list[str] = []
    is_xlsx = kind == "xlsx"

    items = doc.iterate_items() if hasattr(doc, "iterate_items") else []
    for entry in items:
        # iterate_items() yields (item, level) in Docling 2.x
        item, level = entry if isinstance(entry, tuple) else (entry, 0)
        label = getattr(getattr(item, "label", None), "value", "") or str(getattr(item, "label", ""))
        page = _page_of(item)
        heading_path = " > ".join(heading_stack) or None

        # Section headers maintain the heading stack (not emitted as their own block).
        if "header" in label.lower() or "title" in label.lower():
            text = getattr(item, "text", "") or ""
            if text:
                heading_stack = heading_stack[: max(level - 1, 0)] + [text]
            continue

        # Tables -> own block, kept structured (markdown KEEPS rows/cols), with cell prov.
        if "table" in label.lower() or hasattr(item, "export_to_markdown"):
            try:
                md = item.export_to_markdown()
            except Exception:  # noqa: BLE001 — fall back to text
                md = getattr(item, "text", "") or ""
            if md:
                sheet = _sheet_name_of(item, doc) if is_xlsx else None
                cell_range = _table_cell_range(item)
                blocks.append(ParsedBlock(
                    text=md, page_number=None if is_xlsx else page,
                    sheet_name=sheet, cell_range=cell_range, is_table=True,
                    heading_path=heading_path, extra={"label": label},
                ))
            continue

        # Plain text.
        text = getattr(item, "text", "") or ""
        if text.strip():
            blocks.append(ParsedBlock(text=text, page_number=page, heading_path=heading_path,
                                      extra={"label": label}))

    # Fallback: if item iteration yielded nothing, use whole-doc markdown.
    if not blocks:
        blocks.append(ParsedBlock(text=doc.export_to_markdown(), heading_path="(root)"))
    return blocks
