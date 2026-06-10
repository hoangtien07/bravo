"""Tests for the grounding/verify gate — catches hallucinated numbers at system level."""
from __future__ import annotations

from decimal import Decimal

from app.data_layer.grounding import verify_numbers
from app.data_layer.semantic import MetricResult


def test_grounded_when_all_numbers_match_engine():
    assert verify_numbers("Doanh thu 1.000.000 VND, biên 12,5%", [1000000, 12.5]).grounded


def test_ambiguous_decimal_disambiguated_by_engine():
    # '2.337' read as decimal because the engine produced 2.337
    assert verify_numbers("Tỷ lệ 2.337 lần", [2.337]).grounded


def test_ambiguous_thousands_disambiguated_by_engine():
    # '2.337' read as thousands because the engine produced 2337
    assert verify_numbers("Số lượng 2.337", [2337]).grounded


def test_hallucinated_number_is_caught():
    v = verify_numbers("Doanh thu 9.999.999 VND", [1000000])
    assert not v.grounded
    assert v.unmatched


def test_no_numbers_is_trivially_grounded():
    assert verify_numbers("Không có số liệu nào.", []).grounded


# --- WP-B: scale-aware (council Critical — chặn tỷ↔triệu, sai 1.000 lần) ---
def test_scale_mismatch_ty_vs_trieu_is_caught():
    eng = [MetricResult(metric_id="dt", value=Decimal("12.5"), provenance="", scale="tỷ")]
    assert not verify_numbers("Doanh thu 12,5 triệu VND", eng).grounded   # sai bội số
    assert verify_numbers("Doanh thu 12,5 tỷ VND", eng).grounded          # đúng bội số


def test_safe_answer_masks_unmatched_number():
    v = verify_numbers("Doanh thu 9.999.999 VND", [1000000])
    assert not v.grounded
    assert "9.999.999" not in v.safe_answer
    assert "[số chưa kiểm chứng]" in v.safe_answer
