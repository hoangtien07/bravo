"""Heading-aware chunking for the BRAVO 10 guides.

The guides use numbered headings ("17.2.3.2. Các thiết lập hệ thống"). Splitting by
SECTION (heading -> next heading) gives topically-coherent chunks + section-level
citations, which retrieves far better than raw per-page blocks. Each section keeps the
page where it STARTS (for citation) and the heading as heading_path.
"""
from __future__ import annotations

import re

from app.ingestion.parser import ParsedBlock

# Numbered heading: >=1 dot (so a bare page number "7" doesn't match), followed by a
# title starting with a letter. e.g. "17.2.3.2. Các thiết lập hệ thống", "16.4 Tổng hợp".
_HEADING = re.compile(r"(?<![\d.])(\d{1,2}(?:\.\d{1,3}){1,4}\.?)\s+(?=[^\d\s])")
# Repeating page header "BRAVO 10 <subtitle> <pageno>" at the start of each page.
_PAGE_HEADER = re.compile(r"^\s*BRAVO\s*10\b.{0,60}?\s\d{1,4}\s", re.IGNORECASE)


_TOC_LEADER = re.compile(r"\.{4,}")  # dotted leaders in table-of-contents


def _is_toc_page(raw: str) -> bool:
    return len(_TOC_LEADER.findall(raw)) >= 5


def _clean(text: str) -> str:
    text = _PAGE_HEADER.sub(" ", text)
    text = _TOC_LEADER.sub(" ", text)  # drop any stray dot-leaders
    return re.sub(r"\s+", " ", text).strip()


def _mk(heading: str | None, body: str, page: int | None) -> ParsedBlock:
    body = body.strip(" .–-")
    full = f"{heading} {body}" if heading else body
    return ParsedBlock(text=full.strip(), page_number=page, heading_path=heading)


def heading_chunk(pages: list[ParsedBlock]) -> list[ParsedBlock]:
    """Re-segment per-page blocks into heading-bounded sections (across pages)."""
    out: list[ParsedBlock] = []
    buf, head = "", None
    start_page = pages[0].page_number if pages else None
    for pb in pages:
        if _is_toc_page(pb.text):  # skip table-of-contents / index pages
            continue
        text = _clean(pb.text)
        idx = 0
        for m in _HEADING.finditer(text):
            buf += " " + text[idx:m.start()]
            if buf.strip():
                out.append(_mk(head, buf, start_page))
            head = m.group(1).strip()
            start_page = pb.page_number
            buf = ""
            idx = m.end()
        buf += " " + text[idx:]
    if buf.strip():
        out.append(_mk(head, buf, start_page))
    return out
