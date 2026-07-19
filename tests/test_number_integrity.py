"""Number-integrity gate (invariant #3, generated-answer side)."""
from __future__ import annotations

from app.rag import number_integrity as ni


def test_money_figures_ignores_codes_dates_rates():
    txt = "Nợ 641: 25,000,000đ, thuế 10%, ngày 04/01, TK 1331, năm 2024."
    # money = 25,000,000 only; account codes 641/1331, rate 10, date 04/01, year 2024 ignored.
    assert ni.money_figures(txt) == {25_000_000}


def test_money_figures_handles_both_separators_and_bare():
    assert ni.money_figures("54.500.000 và 5450000") == {54_500_000, 5_450_000}


def test_violations_flags_ungrounded_number():
    question = "số tiền 54,500,000 chịu thuế 10%"
    context = "[1] Hướng dẫn nhập phiếu chi."
    allowed = ni.allowed_from(question, context, "")
    # a self-computed pre-tax figure never given/derived by the engine -> flagged
    answer = "Tiền trước thuế = 49,050,000; tổng 54,500,000."
    assert ni.violations(answer, allowed) == [49_050_000]


def test_violations_empty_when_all_traceable():
    facts = "Thuế 5,450,000; tổng 59,950,000"
    allowed = ni.allowed_from("số tiền 54,500,000", "", facts)
    answer = "VAT 5,450,000, tổng thanh toán 59,950,000, tiền hàng 54,500,000."
    assert ni.violations(answer, allowed) == []


def test_strip_markers_removes_engine_label():
    a = "Số tiền 54,500,000đ [SỐ LIỆU ĐÃ ĐƯỢC MONEY-ENGINE TÍNH]."
    assert "MONEY-ENGINE" not in ni.strip_markers(a)
    assert "54,500,000" in ni.strip_markers(a)


def test_strip_markers_removes_short_engine_label_but_keeps_citations():
    a = "Tổng 59,950,000 [SỐ LIỆU MONEY-ENGINE], theo hướng dẫn [3]."
    out = ni.strip_markers(a)
    assert "MONEY-ENGINE" not in out
    assert "[3]" in out  # citation tag preserved


def test_mask_replaces_only_ungrounded_money():
    allowed = ni.allowed_from("số tiền 54,500,000", "", "")
    masked, ung = ni.mask("Trước thuế 49,050,000; tổng 54,500,000.", allowed)
    assert ung == [49_050_000]
    assert ni.MASK in masked          # the invented figure is masked
    assert "54,500,000" in masked      # the grounded figure survives
    assert "49,050,000" not in masked


def test_mask_noop_when_all_grounded():
    allowed = ni.allowed_from("", "Tổng 59,950,000 và 54,500,000", "")
    masked, ung = ni.mask("Tổng 59,950,000, tiền hàng 54,500,000.", allowed)
    assert ung == [] and masked == "Tổng 59,950,000, tiền hàng 54,500,000."
