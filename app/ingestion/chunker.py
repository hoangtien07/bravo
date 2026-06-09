"""Chunking (token-aware, heading-aligned; derived from docsgpt MIT).

Tables become their OWN chunks (never split mid-table) — findings/B: text-only RAG
fails on tables. Provenance is preserved from ParsedBlock onto each chunk.
"""
from __future__ import annotations

from dataclasses import replace

import tiktoken

from app.ingestion.parser import ParsedBlock

_enc = tiktoken.get_encoding("cl100k_base")
MAX_TOKENS = 1000
MIN_TOKENS = 120


def _ntok(text: str) -> int:
    return len(_enc.encode(text))


def chunk(blocks: list[ParsedBlock]) -> list[ParsedBlock]:
    """Split blocks into chunks. Tables kept whole; long text split on token budget."""
    out: list[ParsedBlock] = []
    for b in blocks:
        if b.is_table or _ntok(b.text) <= MAX_TOKENS:
            out.append(b)
            continue
        # Naive split on paragraphs respecting MAX_TOKENS (TODO: heading-aware split).
        buf, count = [], 0
        for para in b.text.split("\n\n"):
            t = _ntok(para)
            if count + t > MAX_TOKENS and buf:
                out.append(replace(b, text="\n\n".join(buf)))
                buf, count = [], 0
            buf.append(para)
            count += t
        if buf:
            out.append(replace(b, text="\n\n".join(buf)))
    return [b for b in out if _ntok(b.text) >= MIN_TOKENS or b.is_table]
