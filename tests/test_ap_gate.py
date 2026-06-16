"""W5.4 — AP gate: chạy MỌI fixture hoá đơn qua pipeline, kiểm bất biến tiền.

HARD-GATE (đúng 100%, CI chặn nếu vỡ):
  - balance_pass_rate: mọi bút toán cân Nợ=Có (Decimal, dung sai 0 đồng).
  - verify: mọi số trên bút toán truy được về số NGUỒN/dẫn-xuất (engine_values) — không bịa.
  - account-valid: mọi TK ∈ TT99 và postable.
SOFT (thông tin, không chặn): account_map_accuracy so ground-truth CHƯA kế toán duyệt.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import yaml

from app.accounting.coa import load_coa
from app.accounting.journal import build_journal_entry
from app.data_layer import money
from app.ingestion.invoice_parser import parse_invoice_xml

_FIX = Path(__file__).parent / "fixtures" / "invoices"
_EXPECTED = yaml.safe_load((_FIX / "expected_journals.yaml").read_text(encoding="utf-8"))
# Fixture hoá đơn HỢP LỆ (loại bad-totals — fixture lỗi để test validator).
_GOOD = sorted(p.name for p in _FIX.glob("inv_*.xml") if "bad" not in p.name)


def test_all_fixtures_balance_and_verify():
    coa = load_coa()
    balanced = 0
    for name in _GOOD:
        inv = parse_invoice_xml((_FIX / name).read_bytes())
        je = build_journal_entry(inv, coa=coa)
        # 1) cân Nợ=Có
        assert money.reconcile(je.total_debit, [l.debit for l in je.lines]), f"{name}: lệch Nợ=Có"
        assert je.total_debit == je.total_credit
        balanced += 1
        ev = set(je.engine_values)
        for l in je.lines:
            amt = l.debit if l.debit > 0 else l.credit
            # 2) verify: số truy được về engine_values (không bịa)
            assert str(amt) in ev, f"{name}: số {amt} không truy về nguồn"
            # 3) account hợp lệ TT99 + postable
            assert coa.is_valid_posting_account(l.account), f"{name}: TK {l.account} không hợp lệ/postable"
    # HARD-GATE: balance_pass_rate == 100%
    assert balanced == len(_GOOD) == 2


def test_account_map_matches_groundtruth_soft():
    """SOFT: map TK khớp ground-truth (thông tin — chưa kế toán duyệt nên không chặn merge)."""
    coa = load_coa()
    mismatches = []
    for name, exp in _EXPECTED.items():
        je = build_journal_entry(parse_invoice_xml((_FIX / name).read_bytes()), coa=coa)
        debits = {l.account: l.debit for l in je.lines if l.debit > 0}
        for acct, amt in exp["debits"].items():
            if debits.get(acct) != Decimal(amt):
                mismatches.append(f"{name}: TK {acct} mong {amt} có {debits.get(acct)}")
        credit = [l for l in je.lines if l.credit > 0][0]
        if credit.account != exp["credit"]:
            mismatches.append(f"{name}: credit mong {exp['credit']} có {credit.account}")
    # Hiện rule v1 khớp ground-truth; nếu sai chỉ cảnh báo (chưa kế toán ký).
    assert not mismatches, "map lệch ground-truth (rule v1 cần kế toán duyệt): " + "; ".join(mismatches)
