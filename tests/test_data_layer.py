"""Tests for the data layer: deterministic calc sandbox + semantic metric layer.

Verifies the ADR-0004/0005 contract: the engine computes numbers (exactly), and
out-of-registry questions ABSTAIN instead of hallucinating.
"""
from __future__ import annotations

import pytest

from app.data_layer import calc, semantic
from app.data_layer.semantic import Metric, MetricQuery


# --- calc sandbox (ADR-0004) ---
def test_calc_basic_arithmetic():
    assert calc.compute("(914 - 391) / 391 * 100", {}) == pytest.approx(133.76, abs=0.01)


def test_calc_with_named_inputs():
    val = calc.compute("rev_2023 / rev_2022", {"rev_2023": 914, "rev_2022": 391})
    assert val == pytest.approx(2.337, abs=0.001)


def test_calc_whitelisted_funcs():
    assert calc.compute("round(margin * 100, 1)", {"margin": 0.12345}) == 12.3


def test_calc_rejects_unsafe():
    for expr in ["__import__('os')", "open('x')", "a.b", "().__class__"]:
        with pytest.raises(calc.CalcError):
            calc.compute(expr, {"a": 1})


def test_calc_unknown_variable_errors():
    with pytest.raises(calc.CalcError):
        calc.compute("revenue * 2", {})


# --- semantic metric layer (ADR-0005) ---
class _MockSource:
    """Stand-in for the ERP-backed DataSource (real impl is Phase 2)."""

    def fetch(self, metric_id, params):
        return 1000.0, f"metric:{metric_id} params={dict(params)}"


def test_semantic_executes_registered_metric():
    semantic.REGISTRY.register(Metric("doanh_thu_thuan", "Doanh thu thuần", ("ky",)))
    res = semantic.execute(MetricQuery("doanh_thu_thuan", {"ky": "2026-Q1"}), _MockSource())
    assert res.value == 1000.0
    assert "doanh_thu_thuan" in res.provenance  # citation/drill-down


def test_semantic_unknown_metric_abstains():
    with pytest.raises(ValueError, match="ABSTAIN"):
        semantic.execute(MetricQuery("bia_so_lieu", {}), _MockSource())


def test_semantic_missing_param_errors():
    semantic.REGISTRY.register(Metric("cong_no", "Công nợ", ("ky",)))
    with pytest.raises(ValueError, match="Thiếu tham số"):
        semantic.execute(MetricQuery("cong_no", {}), _MockSource())


def test_semantic_answer_abstains_when_no_metric_maps():
    # plan_fn returns None => out of scope => abstain (no hallucinated number)
    assert semantic.answer("câu hỏi linh tinh", _MockSource(), plan_fn=lambda q: None) is None
