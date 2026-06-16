"""W1.3 — parser hoá đơn điện tử XML (TT78) + validator deterministic."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.ingestion.invoice_parser import (
    parse_invoice_xml,
    valid_mst,
    validate_invoice,
)

_FIX = Path(__file__).parent / "fixtures" / "invoices"


def _load(name: str):
    return parse_invoice_xml((_FIX / name).read_bytes(), raw_xml_path=str(_FIX / name))


def test_mst_checksum():
    assert valid_mst("0100100008") and valid_mst("0300120019")
    assert not valid_mst("0100100000")   # sai check digit
    assert not valid_mst("12345")        # sai độ dài


def test_parse_single_invoice():
    inv = _load("inv_single_10pct_goods.xml")
    assert inv.so_hoa_don == "0000123"
    assert inv.mst_ban == "0100100008" and inv.mst_mua == "0300120019"
    assert inv.currency == "VND"
    assert len(inv.lines) == 1
    ln = inv.lines[0]
    assert ln.ten_hang == "Hàng hóa thương mại X"
    assert ln.thanh_tien == Decimal("1000000") and ln.tien_thue == Decimal("100000")
    assert ln.thue_suat == "10" and ln.source_ref == "HHDVu[1]"
    assert inv.tong_tien_hang == Decimal("1000000")
    assert inv.tong_thanh_toan == Decimal("1100000")


def test_validate_clean_invoice():
    assert validate_invoice(_load("inv_single_10pct_goods.xml")) == []
    assert validate_invoice(_load("inv_multi_rate.xml")) == []


def test_multi_rate_lines():
    inv = _load("inv_multi_rate.xml")
    assert len(inv.lines) == 2
    assert {ln.thue_suat for ln in inv.lines} == {"8", "10"}
    assert inv.tong_tien_hang == Decimal("1500000")


def test_validate_flags_bad_totals():
    flags = validate_invoice(_load("inv_bad_totals.xml"))
    assert any("tổng thanh toán" in f.lower() for f in flags), flags


def test_source_numbers_for_verify_gate():
    inv = _load("inv_single_10pct_goods.xml")
    nums = inv.source_numbers()
    # mọi số nguồn có mặt để verify-gate dùng làm engine base values
    assert Decimal("1000000") in nums and Decimal("100000") in nums
    assert Decimal("1100000") in nums
