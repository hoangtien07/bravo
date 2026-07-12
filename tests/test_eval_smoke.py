"""F10: keep the eval harnesses from silently rotting into dead code.

parity_bench + retrieval_eval need external data (BravoGen answers / a live corpus) to RUN, so
they can't be a CI *gate* — but an import smoke test ensures a refactor can't break them unnoticed.
"""
from __future__ import annotations

import importlib


def test_parity_bench_importable_and_runnable():
    mod = importlib.import_module("app.eval.parity_bench")
    assert callable(mod.main)          # `python -m app.eval.parity_bench <questions.yaml>`
    assert callable(mod.run_parity)


def test_retrieval_eval_importable():
    mod = importlib.import_module("app.eval.retrieval_eval")
    assert mod is not None
