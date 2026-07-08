"""Governance cho rule-as-data (Phase 1): chọn theo hiệu lực + fail-loud khi chưa duyệt."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from app.accounting import rules_governance as gov
from app.accounting.account_mapper import tscd_value_threshold
from app.accounting.journal import vat_noncash_threshold


# --- effective-date selection (vá 🔴 chứng từ giáp ranh kỳ) ---
def test_vat_rates_by_effective_date():
    before = set(gov.statutory_field("vat_valid_rates", "rates", dt.date(2020, 1, 1)))
    after = set(gov.statutory_field("vat_valid_rates", "rates", dt.date(2026, 1, 1)))
    assert before == {0, 5, 10}          # trước NQ giảm 8%
    assert after == {0, 5, 8, 10}        # 2022+ có 8%


def test_statutory_latest_when_as_of_none():
    assert set(gov.statutory_field("vat_valid_rates", "rates")) == {0, 5, 8, 10}


def test_thresholds_latest_values():
    assert tscd_value_threshold() == Decimal("30000000")     # TT45
    assert vat_noncash_threshold() == Decimal("20000000")    # TT219
    # đường dated cũng trả đúng cho chứng từ 2026
    assert tscd_value_threshold(dt.date(2026, 2, 12)) == Decimal("30000000")


def test_as_of_from_iso_lenient():
    assert gov.as_of_from_iso("2026-02-12") == dt.date(2026, 2, 12)
    assert gov.as_of_from_iso(None) is None
    assert gov.as_of_from_iso("rác") is None


# --- fail-loud khi chưa duyệt / thiếu header (prod) ---
_OK_HEADER = {"version": "v", "effective_from": "2026-01-01", "reviewed_by": "kt",
              "approved_for_prod": True, "legal_basis": "x"}


def test_prod_rejects_unapproved(monkeypatch):
    monkeypatch.setattr(gov, "_is_prod", lambda: True)
    with pytest.raises(gov.GovernanceError):
        gov.validate_header("x.yaml", {**_OK_HEADER, "approved_for_prod": False})


def test_prod_rejects_missing_header(monkeypatch):
    monkeypatch.setattr(gov, "_is_prod", lambda: True)
    with pytest.raises(gov.GovernanceError):
        gov.validate_header("x.yaml", {"version": "v"})


def test_prod_accepts_approved(monkeypatch):
    monkeypatch.setattr(gov, "_is_prod", lambda: True)
    gov.validate_header("x.yaml", _OK_HEADER)   # không raise


def test_local_only_warns(monkeypatch):
    monkeypatch.setattr(gov, "_is_prod", lambda: False)
    gov.validate_header("x.yaml", {"version": "v"})   # thiếu header nhưng local -> chỉ cảnh báo
