"""Xuất bút toán nháp ra CSV (ADR-0016) — số phải khớp payload, có BOM cho Excel."""
from __future__ import annotations

from pathlib import Path

from app.accounting.journal import build_journal_entry
from app.accounting.journal_export import journal_to_rows, to_csv
from app.ingestion.invoice_parser import parse_invoice_xml

_FIX = Path(__file__).parent / "fixtures" / "invoices"


def _payload() -> dict:
    je = build_journal_entry(parse_invoice_xml((_FIX / "inv_single_10pct_goods.xml").read_bytes()))
    return je.model_dump(mode="json")


def test_csv_has_bom_and_balances():
    data = to_csv(_payload())
    assert data[:3] == b"\xef\xbb\xbf"  # BOM UTF-8 -> Excel đọc tiếng Việt đúng
    text = data.decode("utf-8-sig")
    assert "1100000" in text  # tổng cân Nợ=Có xuất hiện
    assert "156" in text and "331" in text  # các TK


def test_rows_cover_all_lines_and_flags():
    payload = _payload()
    rows = journal_to_rows(payload)
    flat = [c for r in rows for c in r]
    for ln in payload["lines"]:
        assert ln["account"] in flat
    # header bút toán có đủ cột
    assert any(r[:1] == ["TK"] for r in rows)
