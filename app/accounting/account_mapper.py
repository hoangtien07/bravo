"""Map hoá đơn -> tài khoản (TT99) — RULE-FIRST. LLM chỉ gợi ý khi rule mơ hồ (sau).

Quyết định map theo rule do kế toán duyệt (mapping_rules_*.yaml) + danh mục TT99. KHÔNG
để LLM quyết tài khoản ở MVP — rule khớp rõ thì auto; không khớp -> default + needs_review
(kế toán sửa ở HITL). VAT đầu vào -> 1331 (hàng/dịch vụ) hoặc 1332 (TSCĐ). Đối ứng -> 331.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.accounting.coa import CoaCatalog, load_coa
from app.ingestion.invoice_parser import Invoice, InvoiceLine

_DATA = Path(__file__).resolve().parent / "data"


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
        if not coa.is_valid_posting_account(acct):
            needs_review = True
            notes.append(f"{ln.source_ref}: TK {acct} không hạch toán-trực-tiếp được trong TT99 (cần duyệt)")
        line_mappings.append(LineMapping(line=ln, debit_account=acct, matched=matched))

    # VAT đầu vào: nếu có dòng map vào TSCĐ (211) -> 1332; ngược lại 1331.
    vat_account = "1332" if any(m.debit_account == "211" for m in line_mappings) else "1331"
    return MappingProposal(
        line_mappings=line_mappings, vat_account=vat_account, credit_account="331",
        needs_review=needs_review, notes=notes,
    )
