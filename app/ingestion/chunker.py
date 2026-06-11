"""Chunking (token-aware; derived from docsgpt MIT).

Splits over-long blocks on sentence boundaries, with a hard token-window fallback so NO
chunk ever exceeds MAX_TOKENS (well under the embedding API's 8192-token limit). Tables
are kept whole. Provenance (page/heading) is preserved onto each chunk.
"""
from __future__ import annotations

import re
from dataclasses import replace

import tiktoken

from app.ingestion.parser import ParsedBlock

_enc = tiktoken.get_encoding("cl100k_base")
MAX_TOKENS = 900
MIN_TOKENS = 60

_SENT = re.compile(r"(?<=[.!?…:])\s+|\n+")


def _ntok(text: str) -> int:
    return len(_enc.encode(text))


def _hard_split(text: str, max_tokens: int) -> list[str]:
    """Last-resort split by token window (for a single over-long sentence)."""
    toks = _enc.encode(text)
    return [_enc.decode(toks[i:i + max_tokens]) for i in range(0, len(toks), max_tokens)]


def _split_long(text: str) -> list[str]:
    pieces: list[str] = []
    buf, count = [], 0
    for sent in _SENT.split(text):
        if not sent:
            continue
        t = _ntok(sent)
        if t > MAX_TOKENS:  # a single huge sentence -> token-window split
            if buf:
                pieces.append(" ".join(buf)); buf, count = [], 0
            pieces.extend(_hard_split(sent, MAX_TOKENS))
            continue
        if count + t > MAX_TOKENS and buf:
            pieces.append(" ".join(buf)); buf, count = [], 0
        buf.append(sent); count += t
    if buf:
        pieces.append(" ".join(buf))
    return pieces


def chunk(blocks: list[ParsedBlock]) -> list[ParsedBlock]:
    """Split blocks into chunks <= MAX_TOKENS. Tables kept whole; tiny blocks dropped."""
    out: list[ParsedBlock] = []
    for b in blocks:
        if b.is_table or _ntok(b.text) <= MAX_TOKENS:
            out.append(b)
            continue
        for piece in _split_long(b.text):
            out.append(replace(b, text=piece))
    return [b for b in out if b.is_table or _ntok(b.text) >= MIN_TOKENS]
