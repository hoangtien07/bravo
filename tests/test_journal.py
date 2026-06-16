"""W3.1/W3.2 — map-TK rule-first + dựng bút toán kép + validator Nợ=Có (ADR-0014)."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.accounting.account_mapper import map_invoice
from app.accounting.journal import (
    InvoiceMeta,
    JournalEntryPayload,
    JournalLine,
    build_journal_entry,
)
from app.ingestion.invoice_parser import parse_invoice_xml

_FIX = Path(__file__).parent / "fixtures" / "invoices"


def _load(name: str):
    return parse_invoice_xml((_FIX / name).read_bytes())


def test_map_single_goods_no_llm():
    inv = _load("inv_single_10pct_goods.xml")
    prop = map_invoice(inv)
    assert prop.line_mappings[0].debit_account == "156"   # "Hàng hóa thương mại"
    assert prop.line_mappings[0].matched is True
    assert prop.vat_account == "1331" and prop.credit_account == "331"
    assert prop.needs_review is False


def test_map_multi_rate():
    inv = _load("inv_multi_rate.xml")
    prop = map_invoice(inv)
    accts = [m.debit_account for m in prop.line_mappings]
    assert accts == ["6427", "152"]   # dịch vụ tư vấn -> 6427; vật tư -> 152


def test_build_balanced_single():
    je = build_journal_entry(_load("inv_single_10pct_goods.xml"))
    assert je.total_debit == je.total_credit == Decimal("1100000")
    debits = {ln.account: ln.debit for ln in je.lines if ln.debit > 0}
    assert debits == {"156": Decimal("1000000"), "1331": Decimal("100000")}
    credit = [ln for ln in je.lines if ln.credit > 0][0]
    assert credit.account == "331" and credit.credit == Decimal("1100000")
    assert je.needs_review is False and je.validation_flags == []


def test_build_balanced_multi_rate():
    je = build_journal_entry(_load("inv_multi_rate.xml"))
    assert je.total_debit == je.total_credit == Decimal("1640000")
    debits = {ln.account: ln.debit for ln in je.lines if ln.debit > 0}
    assert debits == {"6427": Decimal("500000"), "152": Decimal("1000000"),
                      "1331": Decimal("140000")}


def test_engine_values_cover_all_journal_numbers():
    je = build_journal_entry(_load("inv_single_10pct_goods.xml"))
    ev = set(je.engine_values)
    for ln in je.lines:
        amt = ln.debit if ln.debit > 0 else ln.credit
        assert str(amt) in ev, f"số {amt} không truy được về engine_values (verify-gate sẽ chặn)"


def test_bad_invoice_still_balances_but_flags():
    je = build_journal_entry(_load("inv_bad_totals.xml"))
    assert je.total_debit == je.total_credit          # cân by-construction
    assert je.needs_review is True
    assert any("tổng" in f.lower() for f in je.validation_flags)


def test_validator_rejects_unbalanced():
    with pytest.raises(ValueError, match="KHÔNG cân"):
        JournalEntryPayload(
            invoice=InvoiceMeta(so_hoa_don="x"),
            lines=[JournalLine(account="156", debit=Decimal("100")),
                   JournalLine(account="331", credit=Decimal("99"))],
            total_debit=Decimal("100"), total_credit=Decimal("99"),
        )


def test_validator_rejects_line_both_sides():
    with pytest.raises(ValueError, match="Nợ HOẶC Có"):
        JournalEntryPayload(
            invoice=InvoiceMeta(so_hoa_don="x"),
            lines=[JournalLine(account="156", debit=Decimal("100"), credit=Decimal("100"))],
            total_debit=Decimal("100"), total_credit=Decimal("100"),
        )
