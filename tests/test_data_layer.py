"""Tests for the data layer: deterministic calc sandbox + semantic metric layer.

Verifies the ADR-0004/0005 contract: the engine computes numbers (exactly), and
out-of-registry questions ABSTAIN instead of hallucinating.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from app.data_layer import calc, semantic
from app.data_layer.semantic import Metric, MetricQuery, MetricResult
from app.security.rls import Identity

_ADMIN = Identity(employee_id=uuid.uuid4(), is_admin=True)


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


# --- semantic metric layer (ADR-0005 + WP-F) ---
class _MockSource:
    """Stand-in for a DataSource: returns a value-object, ignores RLS (admin tests)."""

    def fetch(self, metric_id, params, identity):
        return MetricResult(
            metric_id=metric_id, value=Decimal("1000"),
            provenance=f"metric:{metric_id} params={dict(params)}",
        )


def test_semantic_executes_registered_metric():
    semantic.REGISTRY.register(Metric("doanh_thu_thuan", "Doanh thu thuần", ("ky",), ("don_vi",)))
    res = semantic.execute(MetricQuery("doanh_thu_thuan", {"ky": "2026-Q1"}), _MockSource(), _ADMIN)
    assert res.value == 1000
    assert "doanh_thu_thuan" in res.provenance  # citation/drill-down


def test_semantic_unknown_metric_abstains():
    with pytest.raises(ValueError, match="ABSTAIN"):
        semantic.execute(MetricQuery("bia_so_lieu", {}), _MockSource(), _ADMIN)


def test_semantic_missing_param_errors():
    semantic.REGISTRY.register(Metric("cong_no", "Công nợ", ("ky",), ("don_vi",)))
    with pytest.raises(ValueError, match="Thiếu tham số"):
        semantic.execute(MetricQuery("cong_no", {}), _MockSource(), _ADMIN)


def test_semantic_register_rejects_missing_scope_columns():
    # WP-F fail-at-load: metric không khai RLS scope -> không cho register.
    with pytest.raises(ValueError, match="scope_columns"):
        semantic.REGISTRY.register(Metric("no_scope", "Thiếu scope", ("ky",)))


def test_semantic_answer_abstains_when_no_metric_maps():
    # plan_fn returns None => out of scope => abstain (no hallucinated number)
    assert semantic.answer("câu hỏi linh tinh", _MockSource(), _ADMIN, plan_fn=lambda q: None) is None
