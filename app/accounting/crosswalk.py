"""Ánh xạ TT200 -> TT99/2025 (Use-case C) — freeze từ sheet 'Sự khác biệt'.

Dùng để: (a) ánh xạ tham chiếu TK kiểu TT200 cũ sang TT99 + ghi chú; (b) CẢNH BÁO khi
một bút toán nhắm TK đã bị BỎ ở TT99 (chặn + HITL). Các thay đổi THEM/BO/KHAC mang
needs_confirm=True — kế toán phải xác nhận, hệ KHÔNG tự suy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_DATA = Path(__file__).resolve().parent / "data"

CHANGES = frozenset({"KHONG_DOI", "DOI_TEN", "THEM", "BO", "KHAC"})


@dataclass(frozen=True)
class CrosswalkEntry:
    code: str
    name_tt200: str | None
    name_tt99: str | None
    change: str            # KHONG_DOI | DOI_TEN | THEM | BO | KHAC
    note: str
    needs_confirm: bool


@dataclass(frozen=True)
class Crosswalk:
    version: str
    by_code: dict[str, CrosswalkEntry]

    def lookup(self, code: str) -> CrosswalkEntry | None:
        return self.by_code.get(str(code).strip())

    def is_removed(self, code: str) -> bool:
        """TK đã BỎ ở TT99 -> không được hạch toán (cảnh báo + HITL)."""
        e = self.by_code.get(str(code).strip())
        return bool(e and e.change == "BO")


@lru_cache
def load_crosswalk(version: str = "v2025") -> Crosswalk:
    raw = yaml.safe_load(
        (_DATA / f"crosswalk_tt200_tt99_{version}.yaml").read_text(encoding="utf-8"))
    by_code = {
        e["code"]: CrosswalkEntry(
            code=e["code"], name_tt200=e.get("name_tt200"), name_tt99=e.get("name_tt99"),
            change=e["change"], note=e.get("note", ""), needs_confirm=bool(e["needs_confirm"]),
        )
        for e in raw["entries"]
    }
    return Crosswalk(version=raw["version"], by_code=by_code)
