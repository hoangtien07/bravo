"""Danh mục tài khoản TT99/2025 — tra cứu CHÍNH XÁC (exact lookup, KHÔNG semantic/RAG).

Embedding một danh mục tài khoản sẽ gây "map gần đúng" = bịa số hiệu TK (vi phạm invariant
#3). Đây là bảng tra O(1) theo số hiệu TK, freeze từ Excel (scripts/build_coa_from_xlsx.py).
Versioned theo hiệu lực để chuẩn bị cho Thông tư sửa đổi sau (chọn version theo kỳ kế toán).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import yaml


@dataclass(frozen=True)
class Account:
    code: str
    name: str
    level: int            # 1 (tổng hợp) | 2 (chi tiết)
    parent: str | None    # TK cấp 1 của một TK cấp 2
    loai: str | None      # tai_san | no_phai_tra | von_chu_so_huu | doanh_thu | chi_phi | xac_dinh_kqkd
    is_postable: bool      # hạch toán trực tiếp được? (cấp-1 có con cấp-2 -> False)


@dataclass(frozen=True)
class CoaCatalog:
    version: str
    effective_from: str
    by_code: dict[str, Account]

    def lookup(self, code: str) -> Account | None:
        return self.by_code.get(str(code).strip())

    def is_valid(self, code: str) -> bool:
        return str(code).strip() in self.by_code

    def is_valid_posting_account(self, code: str) -> bool:
        """True chỉ khi TK tồn tại VÀ hạch toán-trực-tiếp được (chặn ghi vào TK tổng hợp)."""
        a = self.by_code.get(str(code).strip())
        return bool(a and a.is_postable)

    def children(self, code: str) -> list[Account]:
        code = str(code).strip()
        return [a for a in self.by_code.values() if a.parent == code]

    def ids(self) -> list[str]:
        return sorted(self.by_code)


@lru_cache
def load_coa(version: str = "v2025") -> CoaCatalog:
    """Nạp danh mục TK đã freeze. fail-closed: file thiếu -> raise (không đoán).

    Qua cổng quản trị (header bắt buộc + fail-loud khi chưa duyệt ở prod) — CoA là tầng LUẬT."""
    fname = f"coa_tt99_{version}.yaml"
    from app.accounting.rules_governance import resolve_data_file, validate_header
    raw = yaml.safe_load(resolve_data_file(fname).read_text(encoding="utf-8"))
    validate_header(fname, raw)
    by_code = {
        a["code"]: Account(
            code=a["code"], name=a["name"], level=int(a["level"]),
            parent=a.get("parent"), loai=a.get("loai"), is_postable=bool(a["is_postable"]),
        )
        for a in raw["accounts"]
    }
    return CoaCatalog(version=raw["version"], effective_from=raw["effective_from"], by_code=by_code)
