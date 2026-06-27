"""Luật định khoản theo văn bản (TT45 TSCĐ, TT219 khấu trừ VAT) + ngữ nghĩa Number-Integrity Gate.

Phản biện hội đồng kế toán (MONEY-ENGINE-ROADMAP §7.3): map TSCĐ theo TÊN là sai (phải theo
ngưỡng ≥30tr/TT45); khấu trừ VAT 1331 VÔ ĐIỀU KIỆN là sai (TT219 Đ.15). Gate "cân Nợ=Có" chỉ
là Number-Integrity, KHÔNG bảo chứng định khoản đúng ngữ nghĩa.

Dựng Invoice trực tiếp (không thêm fixture XML) để không đụng hard-gate `== 2` của test_ap_gate.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.accounting.account_mapper import TSCD_VALUE_THRESHOLD, map_invoice
from app.accounting.journal import VAT_NONCASH_THRESHOLD, build_journal_entry
from app.ingestion.invoice_parser import Invoice, InvoiceLine, parse_invoice_xml

_FIX = Path(__file__).parent / "fixtures" / "invoices"


def _line(ten: str, thanh_tien: str, rate: str = "10") -> InvoiceLine:
    tt = Decimal(thanh_tien)
    return InvoiceLine(
        stt=1, ten_hang=ten, dvt="cái", so_luong=Decimal(1), don_gia=tt,
        thanh_tien=tt, thue_suat=rate, tien_thue=(tt * Decimal(rate) / 100),
        source_ref="HHDVu[1]",
    )


def _invoice(line: InvoiceLine) -> Invoice:
    hang = line.thanh_tien or Decimal(0)
    thue = line.tien_thue or Decimal(0)
    return Invoice(
        mau_so="1", ky_hieu="C25TAA", so_hoa_don="123", ngay_lap="2026-02-01", currency="VND",
        mst_ban=None, ten_ban="CTY TEST", mst_mua=None, ten_mua=None, lines=[line],
        tong_tien_hang=hang, tong_tien_thue=thue, tong_thanh_toan=hang + thue,
        source_hash="deadbeef",
    )


# ---- TT45: TSCĐ theo NGƯỠNG GIÁ TRỊ, không theo tên ---------------------------------------
def test_tscd_below_threshold_not_booked_as_fixed_asset():
    """Máy móc < 30tr: dù tên là 'máy móc thiết bị' vẫn KHÔNG được vào 211."""
    prop = map_invoice(_invoice(_line("Máy móc thiết bị mini", "20000000")))
    m = prop.line_mappings[0]
    assert m.debit_account != "211"
    assert m.debit_account == "153"          # tạm xếp CCDC chờ kế toán
    assert m.matched is False and prop.needs_review is True
    assert prop.vat_account == "1331"        # không TSCĐ -> VAT 1331, không 1332
    assert any("30tr" in n or "TSCĐ" in n for n in prop.notes)


def test_tscd_above_threshold_books_211_but_flags_useful_life():
    """Máy móc ≥ 30tr: vào 211 + VAT 1332, NHƯNG cờ điều kiện thời gian sử dụng > 1 năm."""
    prop = map_invoice(_invoice(_line("Máy móc thiết bị sản xuất", "50000000")))
    m = prop.line_mappings[0]
    assert m.debit_account == "211"
    assert prop.vat_account == "1332"
    assert prop.needs_review is True
    assert any("thời gian sử dụng" in n for n in prop.notes)


def test_tscd_threshold_constant_is_30m():
    assert TSCD_VALUE_THRESHOLD == Decimal("30000000")


# ---- TT219 Đ.15: khấu trừ VAT đầu vào CÓ ĐIỀU KIỆN --------------------------------------
def test_vat_large_invoice_flags_noncash_condition():
    """Hoá đơn ≥20tr: bút toán phải CỜ yêu cầu chứng từ thanh toán không tiền mặt."""
    je = build_journal_entry(_invoice(_line("Hàng hóa thương mại", "30000000")))
    assert je.total_debit == je.total_credit            # vẫn cân (number-integrity)
    assert je.needs_review is True
    assert any("tiền mặt" in f for f in je.validation_flags)
    assert VAT_NONCASH_THRESHOLD == Decimal("20000000")


def test_vat_small_invoice_has_no_noncash_flag():
    """Regression: hoá đơn nhỏ (<20tr) KHÔNG bị cờ điều kiện không-tiền-mặt (tránh nhiễu)."""
    je = build_journal_entry(parse_invoice_xml((_FIX / "inv_single_10pct_goods.xml").read_bytes()))
    assert not any("tiền mặt" in f for f in je.validation_flags)
    assert je.needs_review is False


# ---- Ngữ nghĩa gate: CÂN không có nghĩa ĐÚNG -------------------------------------------
def test_number_integrity_gate_allows_balanced_but_flagged_entry():
    """Bút toán CÂN + có cờ ngữ nghĩa vẫn DỰNG ĐƯỢC (gate không chặn ngữ nghĩa, chỉ chặn số)."""
    je = build_journal_entry(_invoice(_line("Hàng hóa thương mại", "30000000")))
    assert je.total_debit == je.total_credit            # gate số: cân
    assert je.needs_review is True                        # nhưng ngữ nghĩa cần người duyệt
    assert je.validation_flags                            # và có cờ — payload không bị raise
