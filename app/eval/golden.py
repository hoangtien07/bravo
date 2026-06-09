"""Golden Q&A schema + scoring (Phase 1E).

Each item: a question, the source(s) that SHOULD be cited, and whether the system
should REFUSE (no grounded answer). Metrics: citation accuracy, refusal correctness.
Generator faithfulness via RAGAS is an optional add-on (findings/J).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GoldenItem:
    question: str
    actor_email: str                 # which seeded user asks (drives RLS scope)
    expected_source_ids: list[str] = field(default_factory=list)
    must_refuse: bool = False        # True => correct behavior is to refuse


@dataclass
class ItemResult:
    item: GoldenItem
    refused: bool
    cited_source_ids: list[str]

    @property
    def refusal_correct(self) -> bool:
        return self.refused == self.item.must_refuse

    @property
    def citation_hit(self) -> bool:
        if self.item.must_refuse:
            return self.refused
        return bool(set(self.cited_source_ids) & set(self.item.expected_source_ids))


def summarize(results: list[ItemResult]) -> dict[str, float]:
    n = len(results) or 1
    return {
        "citation_accuracy": sum(r.citation_hit for r in results) / n,
        "refusal_accuracy": sum(r.refusal_correct for r in results) / n,
        "n": float(len(results)),
    }
