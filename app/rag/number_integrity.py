"""Number-integrity gate for GENERATED answers (invariant #3, retrieval side).

The accounting money-engine (app/accounting/journal.py) already guarantees that DRAFT postings
never contain an invented number. This module is the analogue for free-text chat answers: it
checks that every MONEY figure the model wrote is traceable to a trusted source — the retrieved
context, the numbers the USER supplied in the question, or authoritative money-engine facts.

It does NOT verify arithmetic. That is the point: a chat model must not be trusted to compute
VAT/totals itself (measured failure: a relaxed prompt back-computed a wrong 49,050,000). Any
derived figure must come from the money-engine facts block, or it is flagged as ungrounded.

Small integers (account codes 641/1331/111, tax rate 10, years) are ignored — only figures that
read as money (grouped thousands, or bare integers ≥ 100,000) are gated.
"""
from __future__ import annotations

import re

# "54,500,000" / "54.500.000" (grouped) OR a bare run of ≥6 digits. Dates (04/01) and
# percentages (10%) don't match; account codes (641, 1331) are < 100000 → not money.
_MONEY_RE = re.compile(r"\d{1,3}(?:[.,]\d{3})+|\d{6,}")
_MONEY_FLOOR = 100_000

# Internal seed markers the model may echo verbatim — any bracketed tag mentioning the engine
# (e.g. "[SỐ LIỆU MONEY-ENGINE]", "[SỐ LIỆU ĐÃ ĐƯỢC MONEY-ENGINE TÍNH]"). Citation tags like
# "[3]" contain no such text and are preserved.
_MARKER_RE = re.compile(r"\s*[\[(][^\])]*money-?engine[^\])]*[\])]", re.IGNORECASE)


def _norm(tok: str) -> int:
    return int(re.sub(r"[.,]", "", tok))


def money_figures(text: str) -> set[int]:
    """All money-scale figures in `text` (normalized to int), figures < floor dropped."""
    return {n for n in (_norm(m) for m in _MONEY_RE.findall(text or "")) if n >= _MONEY_FLOOR}


def allowed_from(*sources: str) -> set[int]:
    """Trusted money figures: the union across question text, retrieved context, engine facts."""
    allowed: set[int] = set()
    for s in sources:
        allowed |= money_figures(s)
    return allowed


def violations(answer: str, allowed: set[int]) -> list[int]:
    """Money figures in `answer` not traceable to any trusted source (sorted, deduped)."""
    return sorted(money_figures(answer) - allowed)


def strip_markers(text: str) -> str:
    """Remove internal seed markers the model echoed into the user-facing answer."""
    return _MARKER_RE.sub("", text or "")
