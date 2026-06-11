"""Semantic / metric layer (ADR-0005, findings/H). Phase 2.

LLM maps a question to an APPROVED metric + parameters; a DataSource computes the value
deterministically (real impl: ERP view / SQL / Cube). The LLM NEVER writes raw SQL and
NEVER produces the number. Questions outside the registry -> ABSTAIN (not free SQL).

This module is ERP-agnostic and testable with a mock DataSource; the real ERP-backed
source (Phase 2, needs BRAVO's ERP API) plugs into the same protocol.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol

from app.data_layer import money

if TYPE_CHECKING:
    from app.security.rls import Identity


@dataclass(frozen=True)
class Metric:
    id: str
    description: str
    required_params: tuple[str, ...] = ()
    # RLS scope-binding (WP-F/ADR-0013): cột scope metric phải lọc theo (department/unit/period).
    # BẮT BUỘC khi register — thiếu => fail-at-load (chống rò scope số liệu khi nối ERP thật).
    scope_columns: tuple[str, ...] = ()
    variant: str | None = None  # nhãn nghĩa: "thuần|gộp", "đã_VAT|chưa_VAT", "dồn_tích|tiền_mặt"


@dataclass(frozen=True)
class MetricQuery:
    metric_id: str
    params: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricResult:
    """Value-object số liệu (WP-B / ADR-0012). Mang ĐƠN VỊ + BỘI SỐ để verify-gate
    chặn nhầm tỷ↔triệu. Tiền là Decimal. value tính theo `scale` (vd value=12.5, scale='tỷ')."""
    metric_id: str
    value: Decimal
    provenance: str  # e.g. "metric:doanh_thu_thuan params={ky:2026-Q1}" -> drill-down
    unit: str = "VND"
    scale: str | None = None       # "đồng"|"nghìn"|"triệu"|"tỷ" — None = đã ở đơn vị cơ sở
    currency: str | None = "VND"
    period: str | None = None
    entity: str | None = None
    variant: str | None = None     # "thuần|gộp", "đã_VAT|chưa_VAT", "dồn_tích|tiền_mặt"
    is_demo: bool = False

    def base_value(self) -> Decimal:
        """Giá trị quy về đơn vị cơ sở (đồng) — dùng cho verify-gate so sánh."""
        return money.D(self.value) * money.scale_factor(self.scale)


class DataSource(Protocol):
    """Computes an approved metric deterministically + applies RLS via `identity`.

    Real impl (BravoErpDataSource) reads ERP views read-only; demo impl (MockDataSource)
    reads a YAML fixture. BOTH return a MetricResult value-object and enforce scope on
    `identity` (sensitive metric -> chỉ phòng có quyền). (WP-F / ADR-0013)
    """

    def fetch(self, metric_id: str, params: Mapping[str, object],
              identity: "Identity") -> MetricResult: ...


class MetricRegistry:
    def __init__(self) -> None:
        self._metrics: dict[str, Metric] = {}

    def register(self, m: Metric) -> None:
        if not m.scope_columns:  # fail-at-load: metric không khai RLS scope -> không cho đăng ký
            raise ValueError(
                f"Metric '{m.id}' thiếu scope_columns — phải khai RLS scope "
                "(department/unit/period) trước khi register (WP-F/ADR-0013)."
            )
        self._metrics[m.id] = m

    def get(self, metric_id: str) -> Metric | None:
        return self._metrics.get(metric_id)

    def ids(self) -> list[str]:
        return sorted(self._metrics)


# Approved financial metrics — defined WITH BRAVO accountants (erp-accounting-expert).
REGISTRY = MetricRegistry()
# Example (real catalog filled in Phase 2 against BRAVO ERP):
# REGISTRY.register(Metric("doanh_thu_thuan", "Doanh thu thuần theo kỳ/đơn vị", ("ky",)))


def execute(mq: MetricQuery, source: DataSource, identity: "Identity") -> MetricResult:
    """Run an approved metric deterministically. Raises if metric unknown or params missing.

    Whitelist + ABSTAIN: metric ngoài registry -> ValueError (không SQL tự do). Số liệu +
    RLS do `source.fetch(..., identity)` lo (source trả MetricResult value-object).
    """
    metric = REGISTRY.get(mq.metric_id)
    if metric is None:
        raise ValueError(f"Metric không được duyệt: {mq.metric_id} (ABSTAIN, không SQL tự do)")
    missing = [p for p in metric.required_params if p not in mq.params]
    if missing:
        raise ValueError(f"Thiếu tham số {missing} cho metric {mq.metric_id}")
    return source.fetch(mq.metric_id, mq.params, identity)


# The LLM mapping: question -> MetricQuery | None. Injected so it routes through the
# local Model Router (sensitive -> local). Returns None => caller ABSTAINS.
PlanFn = Callable[[str], "MetricQuery | None"]


def answer(question: str, source: DataSource, identity: "Identity",
           plan_fn: PlanFn) -> MetricResult | None:
    """Plan (LLM picks metric) -> execute (engine computes + RLS). None => abstain (no bịa số)."""
    mq = plan_fn(question)
    if mq is None:
        return None
    return execute(mq, source, identity)
