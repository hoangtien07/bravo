"""W1.1/W1.2 — danh mục TK TT99 + crosswalk TT200->TT99 (freeze từ Excel thật)."""
from __future__ import annotations

from app.accounting.coa import load_coa
from app.accounting.crosswalk import CHANGES, load_crosswalk


def test_coa_loads_and_has_71_level1():
    coa = load_coa()
    level1 = [a for a in coa.by_code.values() if a.level == 1]
    assert len(level1) == 71, f"TT99 phải có 71 TK cấp 1, có {len(level1)}"
    assert coa.version.startswith("TT99")


def test_coa_known_accounts():
    coa = load_coa()
    assert coa.lookup("111").name == "Tiền mặt"
    assert coa.lookup("112").name == "Tiền gửi không kỳ hạn"   # TT99 đổi tên
    assert coa.lookup("1331").loai == "tai_san"
    assert coa.lookup("331").loai == "no_phai_tra"
    assert coa.lookup("632").loai == "chi_phi"


def test_coa_removed_accounts_absent():
    coa = load_coa()
    for code in ("611", "631", "441", "461", "466"):
        assert not coa.is_valid(code), f"TK {code} đã bỏ ở TT99 — không được có trong CoA"


def test_coa_postable_rules():
    coa = load_coa()
    # TK tổng hợp có con cấp-2 -> KHÔNG hạch toán trực tiếp
    assert coa.lookup("133").is_postable is False        # có 1331/1332
    assert coa.is_valid_posting_account("1331") is True  # cấp-2 chi tiết
    assert coa.is_valid_posting_account("133") is False
    assert coa.is_valid_posting_account("999") is False  # không tồn tại


def test_crosswalk_changes():
    cw = load_crosswalk()
    assert cw.lookup("112").change == "DOI_TEN"
    assert cw.lookup("1383").change == "THEM" and cw.lookup("1383").needs_confirm
    assert cw.lookup("1385").change == "BO" and cw.is_removed("1385")
    assert all(e.change in CHANGES for e in cw.by_code.values())
