"""Grounding & abstain/verify gate (findings/H). Phase 2.

Abstention/verification is done at the SYSTEM level — NOT by trusting the model
(reasoning fine-tuning REDUCES abstention 24%). Every number an answer states must map
to a value the engine actually produced; an unmatched number -> the answer is NOT
grounded and must be masked / regenerated / refused.

Vietnamese number formats are ambiguous ('2.337' = 2337 thousands OR 2.337 decimal).
We DISAMBIGUATE using the engine values: a token matches if ANY of its valid
interpretations equals an engine value (within tolerance). This avoids false alarms
while still catching truly invented numbers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_NUM_RE = re.compile(r"-?\d[\d.,]*\d|\d")
_THOUSANDS = re.compile(r"-?\d{1,3}(\.\d{3})+")


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


def extract_numbers(text: str) -> list[float]:
    """Primary (best-guess) interpretation per token — for display/logging."""
    return [c[0] for c in (_candidates(m.group()) for m in _NUM_RE.finditer(text)) if c]


@dataclass
class GroundingVerdict:
    grounded: bool
    unmatched: list[str] = field(default_factory=list)

    @property
    def reason(self) -> str:
        if self.grounded:
            return "Mọi số trong câu trả lời khớp giá trị do engine tính."
        return f"Số không truy được về nguồn (nghi bịa): {self.unmatched}"


def verify_numbers(answer: str, engine_values: list[float], *, rel_tol: float = 1e-4,
                   abs_tol: float = 0.5) -> GroundingVerdict:
    """Every number stated in `answer` must match (any interpretation) an engine value."""
    allowed = list(engine_values)
    unmatched: list[str] = []
    for m in _NUM_RE.finditer(answer):
        token = m.group()
        cands = _candidates(token)
        if not any(abs(n - v) <= max(abs_tol, abs(v) * rel_tol) for n in cands for v in allowed):
            unmatched.append(token)
    return GroundingVerdict(grounded=not unmatched, unmatched=unmatched)
