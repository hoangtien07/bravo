"""Generator faithfulness via RAGAS (findings/J) — optional, needs a judge LLM.

Faithfulness = does the answer stay grounded in the retrieved context (no invented
claims). Run periodically (not every PR — RAGAS correlates ~0.55 with humans, so it
complements, not replaces, the deterministic citation/refusal gate.)

For data sovereignty, the judge LLM should be local (or only non-sensitive/synthetic
samples sent to cloud) — wire the judge through app.llm.router.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FaithfulnessSample:
    question: str
    answer: str
    contexts: list[str]


def score(samples: list[FaithfulnessSample]) -> float:
    """Mean faithfulness over samples (0..1). Lazy-imports ragas.

    TODO(Phase 1E+): configure RAGAS to use a LOCAL judge LLM (sovereignty) instead of
    the default OpenAI judge. Until configured, this raises to avoid silent cloud calls.
    """
    raise NotImplementedError(
        "Configure RAGAS with a local judge LLM (app.llm.router) before enabling — "
        "must not send sensitive context to a default cloud judge (ADR-0003)."
    )
