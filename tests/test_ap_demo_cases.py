"""Các ca hoá đơn DEMO (tests/fixtures/invoices_demo) — show hết gate định khoản cho demo AP.

Tách khỏi tests/fixtures/invoices/ để không đụng hard-gate `== 2` của test_ap_gate.
"""
from __future__ import annotations

from pathlib import Path

from app.accounting.account_mapper import map_invoice
from app.accounting.journal import build_journal_entry
from app.ingestion.invoice_parser import parse_invoice_xml

_FIX = Path(__file__).parent / "fixtures" / "invoices_demo"


def _load(name: str):
    return parse_invoice_xml((_FIX / f"{name}.xml").read_bytes())


def test_tscd_over30m_211_1332_and_flags():
    prop = map_invoice(_load("tscd_over30m"))
    assert prop.line_mappings[0].debit_account == "211"
    assert prop.vat_account == "1332"
    je = build_journal_entry(_load("tscd_over30m"))
    assert je.needs_review is True
    assert any("thời gian sử dụng" in f for f in je.validation_flags)  # TT45
    assert any("tiền mặt" in f for f in je.validation_flags)           # TT219 (≥20tr)
    assert je.invoice_lines and je.invoice_lines[0]["ten_hang"].startswith("Máy móc")


def test_tscd_under30m_reclassified_153():
    prop = map_invoice(_load("tscd_under30m"))
    assert prop.line_mappings[0].debit_account == "153"   # KHÔNG vào 211
    assert prop.vat_account == "1331"
    je = build_journal_entry(_load("tscd_under30m"))
    assert je.needs_review is True
    assert not any("tiền mặt" in f for f in je.validation_flags)       # <20tr


def test_vat_over20m_flags_noncash():
    prop = map_invoice(_load("vat_over20m"))
    assert prop.line_mappings[0].debit_account == "156"
    je = build_journal_entry(_load("vat_over20m"))
    assert any("tiền mặt" in f for f in je.validation_flags)


def test_rule_miss_default_needs_review():
    prop = map_invoice(_load("rule_miss"))
    assert prop.line_mappings[0].debit_account == "6428"
    assert prop.line_mappings[0].matched is False
    assert prop.needs_review is True
