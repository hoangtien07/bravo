"""Map hoá đơn -> tài khoản (TT99) — RULE-FIRST. LLM chỉ gợi ý khi rule mơ hồ (sau).

Quyết định map theo rule do kế toán duyệt (mapping_rules_*.yaml) + danh mục TT99. KHÔNG
để LLM quyết tài khoản ở MVP — rule khớp rõ thì auto; không khớp -> default + needs_review
(kế toán sửa ở HITL). VAT đầu vào -> 1331 (hàng/dịch vụ) hoặc 1332 (TSCĐ). Đối ứng -> 331.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import yaml

from app.accounting.coa import CoaCatalog, load_coa
from app.ingestion.invoice_parser import Invoice, InvoiceLine

_DATA = Path(__file__).resolve().parent / "data"

# TT45/2013 Đ.3: ghi nhận TSCĐ hữu hình chỉ khi nguyên giá ≥ 30 triệu ĐỒNG VÀ thời gian sử
# dụng > 1 năm. Tên hàng KHÔNG đủ kết luận TSCĐ — đây là lỗi định khoản hay gặp. Ngưỡng giá
# trị kiểm được tất định; điều kiện thời gian KHÔNG suy ra được từ hoá đơn -> cờ chờ kế toán.
TSCD_VALUE_THRESHOLD = Decimal("30000000")


def _is_fixed_asset(code: str) -> bool:
    """TK TSCĐ hữu hình: 211 và các tiểu khoản 211x (TT99)."""
    c = str(code).strip()
    return c == "211" or c.startswith("211")


@dataclass(frozen=True)
class _Rule:
    pattern: re.Pattern
    account: str


@lru_cache
def _load_rules(version: str = "v1") -> tuple[str, tuple[_Rule, ...]]:
    raw = yaml.safe_load((_DATA / f"mapping_rules_{version}.yaml").read_text(encoding="utf-8"))
    rules = tuple(_Rule(re.compile(r["match"], re.IGNORECASE), r["account"]) for r in raw["rules"])
    return raw["default_account"], rules


@dataclass
class LineMapping:
    line: InvoiceLine
    debit_account: str
    matched: bool          # rule khớp rõ (False = dùng default -> cần duyệt)


@dataclass
class MappingProposal:
    line_mappings: list[LineMapping]
    vat_account: str       # 1331 (hàng/dịch vụ) | 1332 (TSCĐ)
    credit_account: str    # 331 phải trả người bán
    needs_review: bool
    notes: list[str]


def map_invoice(inv: Invoice, *, coa: CoaCatalog | None = None, version: str = "v1") -> MappingProposal:
    coa = coa or load_coa()
    default_acct, rules = _load_rules(version)
    notes: list[str] = []
    needs_review = False
    line_mappings: list[LineMapping] = []

    for ln in inv.lines:
        name = ln.ten_hang or ""
        acct, matched = default_acct, False
        for r in rules:
            if r.pattern.search(name):
                acct, matched = r.account, True
                break
        if not matched:
            needs_review = True
            notes.append(f"{ln.source_ref}: tên '{name[:40]}' không khớp rule -> mặc định {acct} (cần duyệt)")
        # TT45: tên hàng KHÔNG làm nên TSCĐ. Khớp rule 211 phải qua NGƯỠNG GIÁ TRỊ ≥30tr; dưới
        # ngưỡng thì KHÔNG là TSCĐ -> tạm xếp 153 (CCDC) + cờ (kế toán có thể đổi 142/242/chi phí).
        if _is_fixed_asset(acct):
            amt = ln.thanh_tien or Decimal(0)
            if amt < TSCD_VALUE_THRESHOLD:
                acct, matched = "153", False
                needs_review = True
                notes.append(
                    f"{ln.source_ref}: '{name[:30]}' nguyên giá {amt:.0f} < 30tr -> KHÔNG đủ điều kiện "
                    f"TSCĐ (TT45); tạm xếp 153/CCDC, kế toán xác nhận (có thể 142/242/chi phí)"
                )
            else:
                needs_review = True
                notes.append(
                    f"{ln.source_ref}: TSCĐ (211) cần xác nhận thời gian sử dụng > 1 năm (TT45) — "
                    f"không suy ra được từ hoá đơn"
                )
        if not coa.is_valid_posting_account(acct):
            needs_review = True
            notes.append(f"{ln.source_ref}: TK {acct} không hạch toán-trực-tiếp được trong TT99 (cần duyệt)")
        line_mappings.append(LineMapping(line=ln, debit_account=acct, matched=matched))

    # VAT đầu vào: nếu có dòng map vào TSCĐ (211/211x) -> 1332; ngược lại 1331.
    vat_account = "1332" if any(_is_fixed_asset(m.debit_account) for m in line_mappings) else "1331"
    return MappingProposal(
        line_mappings=line_mappings, vat_account=vat_account, credit_account="331",
        needs_review=needs_review, notes=notes,
    )
