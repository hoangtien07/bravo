"""Golden regression cho AP + tính nhất quán DỮ LIỆU luật (Phase 1).

Bắt hồi quy khi đổi rule-as-data: (1) mọi hoá đơn demo -> bút toán CÂN (Number-Integrity), số
truy được về engine_values; (2) crosswalk TT200->TT99 nhất quán (KHONG_DOI => tên khớp) — chặn
lỗi dữ liệu như 6415 (từng gắn KHONG_DOI nhưng đổi tên); (3) mọi file rule mang header quản trị."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import yaml

from app.accounting.journal import build_journal_entry
from app.accounting.rules_governance import _REQUIRED_HEADER
from app.data_layer import money
from app.ingestion.invoice_parser import parse_invoice_xml

_FIX = Path(__file__).parent / "fixtures" / "invoices_demo"
_DATA = Path(__file__).parents[1] / "app" / "accounting" / "data"


def _je(name: str):
    return build_journal_entry(parse_invoice_xml((_FIX / f"{name}.xml").read_bytes()))


# --- (1) Golden: mọi hoá đơn demo -> bút toán CÂN + số truy nguồn ---
def test_all_demo_invoices_balanced_and_grounded():
    for name in ("tscd_over30m", "tscd_under30m", "vat_over20m", "rule_miss"):
        je = _je(name)
        d = money.money_sum([ln.debit for ln in je.lines])
        c = money.money_sum([ln.credit for ln in je.lines])
        assert d == c == Decimal(str(je.total_debit)), f"{name}: bút toán không cân"
        # Mọi số Nợ/Có phải nằm trong engine_values (không bịa số — invariant #3).
        ev = set(je.engine_values)
        for ln in je.lines:
            amt = ln.debit if ln.debit > 0 else ln.credit
            assert str(money.D(amt)) in ev, f"{name}: số {amt} không truy được engine_values"


# --- (2) Crosswalk TT200->TT99 nhất quán (chặn lỗi 6415-class) ---
def test_crosswalk_khongdoi_names_match():
    raw = yaml.safe_load((_DATA / "crosswalk_tt200_tt99_v2025.yaml").read_text(encoding="utf-8"))
    bad = [e["code"] for e in raw["entries"]
           if e.get("change") == "KHONG_DOI" and e.get("name_tt200") != e.get("name_tt99")]
    assert not bad, f"KHONG_DOI nhưng tên đổi (cần sửa change/needs_confirm): {bad}"


# --- (3) Mọi file rule mang header quản trị (rule-as-data governance) ---
def test_all_rule_files_have_governance_header():
    for fname in ("statutory_rules_vn.yaml", "mapping_rules_v1.yaml",
                  "coa_tt99_v2025.yaml", "crosswalk_tt200_tt99_v2025.yaml"):
        raw = yaml.safe_load((_DATA / fname).read_text(encoding="utf-8"))
        missing = [k for k in _REQUIRED_HEADER if k not in raw]
        assert not missing, f"{fname} thiếu header quản trị: {missing}"
