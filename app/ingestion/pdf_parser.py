"""Lightweight PDF parser (pypdf) for the BRAVO 10 user-guide corpus.

Chosen over Docling for digital text PDFs after testing on the real corpus: pypdf
extracts Vietnamese diacritics cleanly (poppler/pdftotext mangled them), is tiny, and
gives per-page text -> natural `page_number` provenance. No OCR (screenshots ignored —
the text carries the knowledge; ADR-0009 descope).

Docling stays available for DOCX/XLSX / table-heavy docs (see parser.py dispatch).
"""
from __future__ import annotations

from pathlib import Path

from app.ingestion.parser import ParsedBlock

_MIN_CHARS = 30  # skip near-empty pages (cover/screenshot-only)


def parse_pdf(path: str | Path) -> list[ParsedBlock]:
    """One ParsedBlock per page, carrying the page number for citations."""
    from pypdf import PdfReader  # lazy import

    reader = PdfReader(str(path))
    blocks: list[ParsedBlock] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if len(text) >= _MIN_CHARS:
            blocks.append(ParsedBlock(text=text, page_number=i))
    return blocks
