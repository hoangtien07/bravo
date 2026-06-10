"""Money & scale helpers (WP-B / ADR-0012). Tiền dùng Decimal — KHÔNG float.

Council Critical: calc dùng float làm tổng KHÔNG khớp chi tiết (cross-foot fail); và
verify-gate so trị tuyệt đối bỏ qua bội số → engine 12.5 'tỷ' mà LLM viết '12,5 triệu'
vẫn lọt (sai 1.000 lần). Hai phòng vệ:
  - Decimal cho mọi phép cộng tiền + reconcile (Σ chi tiết == tổng, dung sai 0 đồng).
  - scale_factor() để quy mọi số về đơn vị cơ sở (đồng) trước khi so sánh.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

# Bội số đơn vị tiếng Việt -> hệ số quy về ĐỒNG (đơn vị cơ sở).
SCALE_FACTOR: dict[str, Decimal] = {
    "": Decimal(1),
    "đồng": Decimal(1),
    "nghìn": Decimal(1_000),
    "ngàn": Decimal(1_000),
    "triệu": Decimal(1_000_000),
    "tỷ": Decimal(1_000_000_000),
    "tỉ": Decimal(1_000_000_000),
}


def D(x: object) -> Decimal:
    """Parse an toàn về Decimal (qua str để tránh nhiễu nhị phân của float)."""
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def scale_factor(scale: str | None) -> Decimal:
    """Hệ số quy về đồng cho một nhãn bội số ('tỷ' -> 1e9). Không rõ -> 1."""
    if scale is None:
        return Decimal(1)
    return SCALE_FACTOR.get(str(scale).strip().lower(), Decimal(1))


def quantize(value: object, places: int = 0) -> Decimal:
    """Làm tròn tường minh ROUND_HALF_UP. VND places=0; ngoại tệ places=2."""
    exp = Decimal(1).scaleb(-places)  # places=0 -> '1'; places=2 -> '0.01'
    return D(value).quantize(exp, rounding=ROUND_HALF_UP)


def money_sum(items: object) -> Decimal:
    """Tổng tiền bằng Decimal (không float drift)."""
    total = Decimal(0)
    for it in items:  # type: ignore[attr-defined]
        total += D(it)
    return total


def reconcile(total: object, parts: object, tol: object = "0") -> bool:
    """Cross-foot: Σ(chi tiết) == tổng (Decimal, dung sai mặc định 0 đồng)."""
    return abs(money_sum(parts) - D(total)) <= D(tol)
