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
from typing import Protocol


@dataclass(frozen=True)
class Metric:
    id: str
    description: str
    required_params: tuple[str, ...] = ()


@dataclass(frozen=True)
class MetricQuery:
    metric_id: str
    params: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricResult:
    metric_id: str
    value: float
    provenance: str  # e.g. "metric:doanh_thu_thuan params={ky:2026-Q1}" -> drill-down


class DataSource(Protocol):
    """Computes an approved metric deterministically. Real impl reads ERP views (read-only)."""

    def fetch(self, metric_id: str, params: Mapping[str, object]) -> tuple[float, str]: ...


class MetricRegistry:
    def __init__(self) -> None:
        self._metrics: dict[str, Metric] = {}

    def register(self, m: Metric) -> None:
        self._metrics[m.id] = m

    def get(self, metric_id: str) -> Metric | None:
        return self._metrics.get(metric_id)

    def ids(self) -> list[str]:
        return sorted(self._metrics)


# Approved financial metrics — defined WITH BRAVO accountants (erp-accounting-expert).
REGISTRY = MetricRegistry()
# Example (real catalog filled in Phase 2 against BRAVO ERP):
# REGISTRY.register(Metric("doanh_thu_thuan", "Doanh thu thuần theo kỳ/đơn vị", ("ky",)))


def execute(mq: MetricQuery, source: DataSource) -> MetricResult:
    """Run an approved metric deterministically. Raises if metric unknown or params missing."""
    metric = REGISTRY.get(mq.metric_id)
    if metric is None:
        raise ValueError(f"Metric không được duyệt: {mq.metric_id} (ABSTAIN, không SQL tự do)")
    missing = [p for p in metric.required_params if p not in mq.params]
    if missing:
        raise ValueError(f"Thiếu tham số {missing} cho metric {mq.metric_id}")
    value, prov = source.fetch(mq.metric_id, mq.params)
    return MetricResult(metric_id=mq.metric_id, value=float(value), provenance=prov)


# The LLM mapping: question -> MetricQuery | None. Injected so it routes through the
# local Model Router (sensitive -> local). Returns None => caller ABSTAINS.
PlanFn = Callable[[str], "MetricQuery | None"]


def answer(question: str, source: DataSource, plan_fn: PlanFn) -> MetricResult | None:
    """Plan (LLM picks metric) -> execute (engine computes). None => abstain (no bịa số)."""
    mq = plan_fn(question)
    if mq is None:
        return None
    return execute(mq, source)
