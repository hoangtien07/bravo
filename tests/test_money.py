"""Tests for Decimal money helpers (WP-B / ADR-0012) — cross-foot + no float drift."""
from __future__ import annotations

from decimal import Decimal

from app.data_layer import money


def test_reconcile_cross_foot():
    assert money.reconcile("52.8", ["45.2", "7.6"])        # Σ == tổng
    assert not money.reconcile("52.8", ["45.2", "7.7"])    # lệch -> từ chối


def test_money_sum_has_no_float_drift():
    assert money.money_sum(["0.1", "0.2"]) == Decimal("0.3")
    assert 0.1 + 0.2 != 0.3  # chứng minh: float DRIFT, Decimal thì không


def test_quantize_vnd_rounds_half_up():
    assert money.quantize("100.5") == Decimal("101")  # ROUND_HALF_UP: .5 lên
    assert money.quantize("100.4") == Decimal("100")
    assert money.quantize("12.345", places=2) == Decimal("12.35")


def test_scale_factor_ty():
    assert money.scale_factor("tỷ") == Decimal(1_000_000_000)
    assert money.scale_factor("triệu") == Decimal(1_000_000)
    assert money.scale_factor(None) == Decimal(1)
