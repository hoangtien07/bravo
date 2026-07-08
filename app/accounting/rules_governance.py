"""Governance cho RULE-AS-DATA (Phase 1 — bản HẸP có cổng).

Mọi file rule kế toán/thuế trong `data/` là DỮ LIỆU có vòng đời pháp lý, KHÔNG phải hằng số
code. Module này là điểm nạp DUY NHẤT, cưỡng chế 3 điều accounting-council yêu cầu:

  1. **Header quản trị bắt buộc** — version + effective_from + reviewed_by + approved_for_prod +
     legal_basis. Thiếu -> fail-loud ở prod (cảnh báo ở local để không cản dev).
  2. **Fail-loud khi chưa duyệt** — prod TỪ CHỐI nạp file `approved_for_prod != true` (mượn tinh
     thần exit-code gate của agent-ai/handover_check). Data-as-truth KHÔNG tự đúng -> cần cổng người.
  3. **Chọn theo NGÀY LẬP chứng từ (as_of)** — tham số LUẬT có nhiều `periods`; chọn phiên bản có
     hiệu lực tại `ngay_lap` hoá đơn, KHÔNG theo ngày hệ thống. Vá lỗi 🔴 chứng từ giáp ranh kỳ
     (vd TT200 15/12/2025 ↔ TT99 05/01/2026 định khoản khác nhau).

Phân tầng rule (accounting-council): STATUTORY (luật — global, khoá) / POLICY (chính sách DN) /
SUGGESTION (gợi ý, luôn kéo needs_review). File này quản tầng STATUTORY + header cho mọi tầng.
"""
from __future__ import annotations

import datetime as _dt
import logging
from functools import lru_cache
from pathlib import Path

import yaml

from app.config import get_settings

_log = logging.getLogger("bravo.governance")
_PKG_DATA = Path(__file__).resolve().parent / "data"      # bản ship in-package (fallback)
_REQUIRED_HEADER = ("version", "effective_from", "reviewed_by", "approved_for_prod", "legal_basis")
_PROD_ENVS = {"staging", "production", "prod"}


def resolve_data_file(filename: str) -> Path:
    """Đường dẫn file rule runtime — OVERLAY trước, fallback in-package (config-as-data, ADR-0018).

    Nếu BRAVO_KNOWLEDGE_DIR được đặt và có file cùng tên -> dùng bản overlay (cập nhật rule không
    rebuild image). Ngược lại -> bản ship in-package (bravo luôn CHẠY ĐƯỢC). Đọc lúc boot, single-
    tenant (KHÔNG resolve per-request -> KHÔNG multi-tenant SaaS, tôn trọng ADR-0016 CUT#7)."""
    override = get_settings().knowledge_dir
    if override:
        cand = Path(override) / filename
        if cand.exists():
            return cand
    return _PKG_DATA / filename


class GovernanceError(RuntimeError):
    """Nạp rule vi phạm cổng quản trị (thiếu header / chưa duyệt ở prod)."""


def _is_prod() -> bool:
    return get_settings().env in _PROD_ENVS


def _parse_date(v) -> _dt.date | None:
    if v is None or v == "":
        return None
    if isinstance(v, _dt.datetime):
        return v.date()
    if isinstance(v, _dt.date):
        return v
    return _dt.date.fromisoformat(str(v)[:10])


def validate_header(name: str, raw: dict) -> None:
    """Cưỡng chế header quản trị. Prod: raise; local: cảnh báo (không cản dev)."""
    missing = [k for k in _REQUIRED_HEADER if k not in raw]
    if missing:
        msg = f"[governance] {name}: thiếu trường header bắt buộc {missing}"
        if _is_prod():
            raise GovernanceError(msg)
        _log.warning(msg)
    if not raw.get("approved_for_prod"):
        msg = (f"[governance] {name}: approved_for_prod != true — CHƯA kế toán duyệt. "
               f"Cấm chạy prod (fail-loud); local chỉ cảnh báo.")
        if _is_prod():
            raise GovernanceError(msg)
        _log.warning(msg)


@lru_cache
def load_governed(filename: str) -> dict:
    """Nạp 1 file rule versioned (overlay-or-package) + kiểm cổng quản trị. Cache theo tên file."""
    raw = yaml.safe_load(resolve_data_file(filename).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise GovernanceError(f"[governance] {filename}: nội dung không phải mapping YAML")
    validate_header(filename, raw)
    return raw


def _pick_period(periods: list[dict], as_of: _dt.date | str | None) -> dict:
    """Chọn period có effective_from muộn nhất mà ≤ as_of. as_of None -> period mới nhất."""
    ordered = sorted(periods, key=lambda p: _parse_date(p["effective_from"]))
    aod = _parse_date(as_of)
    if aod is None:
        return ordered[-1]
    chosen = None
    for p in ordered:
        if _parse_date(p["effective_from"]) <= aod:
            chosen = p
    return chosen if chosen is not None else ordered[0]


@lru_cache
def _statutory() -> dict:
    return load_governed("statutory_rules_vn.yaml")


def statutory_field(key: str, field: str, as_of: _dt.date | str | None = None):
    """Giá trị tham số LUẬT `key` (field trong period) hiệu lực tại `as_of` (None = mới nhất)."""
    block = _statutory()["rules"][key]
    return _pick_period(block["periods"], as_of)[field]


def as_of_from_iso(value: str | None) -> _dt.date | None:
    """Parse `ngay_lap` (ISO 'YYYY-MM-DD…') an toàn -> date | None (không rõ -> None = mới nhất)."""
    try:
        return _dt.date.fromisoformat((value or "")[:10])
    except (ValueError, TypeError):
        return None
