"""Grounding & abstain/verify gate (ADR-0012, findings/H). Phase 2.

Abstention/verification is done at the SYSTEM level — NOT by trusting the model
(reasoning fine-tuning REDUCES abstention 24%). Every number an answer states must map
to a value the engine actually produced; an unmatched number -> the answer is NOT
grounded and must be masked / regenerated / refused.

WP-B (council Critical): compare in the BASE unit (đồng), reading the SCALE WORD next to
each number ('triệu' -> x1e6, 'tỷ' -> x1e9). This catches the '12.5 tỷ' engine vs
'12,5 triệu' answer mistake (off by 1.000x) that a magnitude-only compare lets through.
`engine_values` accept either plain floats (already base) or MetricResult value-objects
(carrying scale). `safe_answer` masks unmatched numbers so the loop can abstain/regenerate.

Vietnamese number formats are ambiguous ('2.337' = 2337 thousands OR 2.337 decimal).
We DISAMBIGUATE using the engine values: a token matches if ANY of its valid
interpretations (x its scale word) equals an engine base value (within tolerance).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_NUM_RE = re.compile(r"-?\d[\d.,]*\d|\d")
_THOUSANDS = re.compile(r"-?\d{1,3}(\.\d{3})+")
# Bội số tiếng Việt đứng NGAY SAU số (chỉ xét từ liền sau, không quét cả câu —
# tránh false-trigger với 'Tỷ lệ ...' đứng TRƯỚC số).
_SCALE_WORDS = {
    "nghìn": 1e3, "ngàn": 1e3, "triệu": 1e6, "tỷ": 1e9, "tỉ": 1e9, "tỳ": 1e9,
}
_WORD_AFTER = re.compile(r"\s+([^\W\d_]+)", re.UNICODE)
_MASK = "[số chưa kiểm chứng]"


def _candidates(token: str) -> list[float]:
    """All valid float interpretations of a VN-formatted number token."""
    t = token.strip()
    has_dot, has_comma = "." in t, "," in t
    cands: list[float] = []

    def _try(s: str) -> None:
        try:
            cands.append(float(s))
        except ValueError:
            pass

    if has_dot and has_comma:
        _try(t.replace(".", "").replace(",", "."))      # 1.234,5 -> 1234.5
    elif has_comma:
        _try(t.replace(",", "."))                        # 12,5 -> 12.5
    elif has_dot:
        if _THOUSANDS.fullmatch(t):
            _try(t.replace(".", ""))                     # thousands: 2.337 -> 2337
        _try(t)                                          # decimal:   2.337 -> 2.337
    else:
        _try(t)
    return cands


def _scale_after(text: str, end: int) -> float:
    """Hệ số của từ bội-số đứng ngay sau số (vd '12,5 triệu' -> 1e6). Không có -> 1."""
    m = _WORD_AFTER.match(text[end:])
    if m:
        return _SCALE_WORDS.get(m.group(1).lower(), 1.0)
    return 1.0


def _engine_bases(engine_values: list) -> list[float]:
    """Quy mọi engine value về đơn vị cơ sở (đồng). float = đã ở base; MetricResult dùng base_value()."""
    bases: list[float] = []
    for v in engine_values:
        if isinstance(v, (int, float)):
            bases.append(float(v))
        elif hasattr(v, "base_value"):
            bases.append(float(v.base_value()))
        else:  # duck-type: object có .value
            bases.append(float(getattr(v, "value", v)))
    return bases


def extract_numbers(text: str) -> list[float]:
    """Primary (best-guess) interpretation per token — for display/logging."""
    return [c[0] for c in (_candidates(m.group()) for m in _NUM_RE.finditer(text)) if c]


@dataclass
class GroundingVerdict:
    grounded: bool
    unmatched: list[str] = field(default_factory=list)
    safe_answer: str = ""

    @property
    def reason(self) -> str:
        if self.grounded:
            return "Mọi số trong câu trả lời khớp giá trị do engine tính."
        return f"Số không truy được về nguồn (nghi bịa): {self.unmatched}"


# Alias theo CONTRACTS §2.5.
VerifyVerdict = GroundingVerdict


def verify_numbers(answer: str, engine_values: list, *, rel_tol: float = 1e-4,
                   abs_tol: float = 0.5) -> GroundingVerdict:
    """Mọi số trong `answer` (x bội-số liền sau) phải khớp một engine base value.

    engine_values: list[float] (đã ở đồng) HOẶC list[MetricResult] (mang scale).
    Trả verdict + safe_answer (đã mask số không khớp) để loop abstain/regenerate.
    """
    bases = _engine_bases(engine_values)
    unmatched: list[str] = []
    spans: list[tuple[int, int]] = []
    for m in _NUM_RE.finditer(answer):
        token = m.group()
        factor = _scale_after(answer, m.end())
        cands = [c * factor for c in _candidates(token)]
        ok = any(
            abs(n - v) <= max(abs_tol, abs(v) * rel_tol)
            for n in cands for v in bases
        )
        if not ok:
            unmatched.append(token)
            spans.append((m.start(), m.end()))

    # Build safe_answer: mask các span không khớp (từ phải sang trái để giữ index).
    safe = answer
    for start, end in reversed(spans):
        safe = safe[:start] + _MASK + safe[end:]
    return GroundingVerdict(grounded=not unmatched, unmatched=unmatched, safe_answer=safe)
