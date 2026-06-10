"""Document parsing (Docling-based, derived from docsgpt MIT).

MVP: DIGITAL documents only (native PDF/DOCX/XLSX with text). NO OCR — scanned-table
OCR is descoped (ADR-0009). Tables are kept STRUCTURED (markdown) — a flattened table
is meaningless for accounting numbers (rag-architect).

Each parsed block carries provenance (page/sheet/cell) so citations are verifiable —
this is the gap docsgpt left; we fill it here (Phase 1B).

NOTE: Docling's item-level API is version-sensitive. The mapping below targets Docling
2.x (`document.iterate_items()`, `*.prov[0].page_no`, TextItem/TableItem/SectionHeaderItem).
Guarded with getattr so it degrades gracefully; verify against the pinned version.
"""
from __future__ import annotations

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


def _page_of(item) -> int | None:
    prov = getattr(item, "prov", None)
    if prov:
        return getattr(prov[0], "page_no", None)
    return None


def parse(path: str | Path) -> list[ParsedBlock]:
    """Parse a digital document into provenance-bearing blocks.

    Dispatch: PDF -> lightweight pypdf parser (clean Vietnamese, page provenance,
    proven on the BRAVO 10 corpus); other formats -> Docling.
    """
    if str(path).lower().endswith(".pdf"):
        from app.ingestion.pdf_parser import parse_pdf
        return parse_pdf(path)

    from docling.document_converter import DocumentConverter  # lazy import

    converter = DocumentConverter()  # OCR disabled by default; table structure on
    result = converter.convert(str(path))
    doc = result.document
    blocks: list[ParsedBlock] = []
    heading_stack: list[str] = []

    items = doc.iterate_items() if hasattr(doc, "iterate_items") else []
    for entry in items:
        # iterate_items() yields (item, level) in Docling 2.x
        item, level = entry if isinstance(entry, tuple) else (entry, 0)
        label = getattr(getattr(item, "label", None), "value", "") or str(getattr(item, "label", ""))
        page = _page_of(item)
        heading_path = " > ".join(heading_stack) or None

        # Section headers maintain the heading stack
        if "header" in label.lower() or "title" in label.lower():
            text = getattr(item, "text", "") or ""
            if text:
                heading_stack = heading_stack[: max(level - 1, 0)] + [text]
            continue

        # Tables -> own block, kept structured (markdown)
        if "table" in label.lower() or hasattr(item, "export_to_markdown"):
            try:
                md = item.export_to_markdown()
            except Exception:  # noqa: BLE001 — fall back to text
                md = getattr(item, "text", "") or ""
            if md:
                blocks.append(ParsedBlock(text=md, page_number=page, is_table=True,
                                          heading_path=heading_path,
                                          extra={"label": label}))
            continue

        # Plain text
        text = getattr(item, "text", "") or ""
        if text.strip():
            blocks.append(ParsedBlock(text=text, page_number=page, heading_path=heading_path,
                                      extra={"label": label}))

    # Fallback: if item iteration yielded nothing, use whole-doc markdown.
    if not blocks:
        blocks.append(ParsedBlock(text=doc.export_to_markdown(), heading_path="(root)"))
    return blocks
    # TODO(Phase 1B+): XLSX sheet_name + cell_range provenance (Docling exposes sheet via
    # table metadata; map to ParsedBlock.sheet_name/cell_range for spreadsheet citations).
