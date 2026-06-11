"""Generator faithfulness judge (findings/J, WP-H) — REUSE ragas/DeepEval, judge LOCAL.

Faithfulness = does the answer stay grounded in the retrieved context (no invented
claims). This is a SOFT signal that complements — does NOT replace — the deterministic
HARD-FAIL gate (RLS-leak / fabricated-number / wrong-unit / egress / injection in
app.eval.passk). RAGAS correlates ~0.55 with humans, so it is run periodically.

Sovereignty (invariant #4): the judge LLM must run LOCAL — never the default OpenAI judge.
`score(...)` wires ragas to a local judge via `judge_llm` (an openai-compatible client
pointed at vLLM/Ollama, e.g. app.llm.router's local backend). If ragas is not installed,
the caller should `pytest.importorskip("ragas")` / skip this branch — the deterministic
gate still runs without it.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FaithfulnessSample:
    question: str
    answer: str
    contexts: list[str]


def ragas_available() -> bool:
    """True if ragas is importable (judge branch can run). Lets callers skip cleanly."""
    try:
        import ragas  # noqa: F401
        return True
    except Exception:
        return False


def score(samples: list[FaithfulnessSample], *, judge_llm=None) -> float:
    """Mean faithfulness over samples (0..1) using a LOCAL judge.

    `judge_llm` MUST be a local (or explicitly-allowed) LLM wrapper — passing None raises,
    so we never silently fall back to ragas' default OpenAI judge (invariant #4 / ADR-0003).
    Lazy-imports ragas so the deterministic gate has no hard ragas dependency.
    """
    if not ragas_available():
        raise RuntimeError(
            "ragas chưa được cài — bỏ qua nhánh judge (importorskip), gate deterministic vẫn chạy."
        )
    if judge_llm is None:
        raise ValueError(
            "judge_llm bắt buộc và phải là LLM CỤC BỘ (vLLM/Ollama qua app.llm.router) — "
            "không dùng judge OpenAI mặc định với ngữ cảnh nhạy cảm (invariant #4 / ADR-0003)."
        )

    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness

    ds = Dataset.from_dict({
        "question": [s.question for s in samples],
        "answer": [s.answer for s in samples],
        "contexts": [s.contexts for s in samples],
    })
    result = evaluate(ds, metrics=[faithfulness], llm=judge_llm)
    return float(result["faithfulness"])
