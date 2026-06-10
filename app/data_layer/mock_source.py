"""MockDataSource — số liệu GIẢ (DEMO) cho Demo B, không cần ERP (WP-F / ADR-0013).

Đọc tests/fixtures/mock_financials_tt99.yaml -> MetricResult value-object (Decimal, scale,
variant, is_demo=True). Áp RLS theo `identity`: chỉ tiêu NHẠY (sensitive) chỉ trả cho phòng
có quyền (vd quy_luong_thang -> nhan_su/giám đốc), phòng khác -> AccessDenied.

Khi ERP thật về: viết BravoErpDataSource cùng Protocol DataSource (semantic.py), đổi 1 dòng
cấu hình — KHÔNG đổi loop/semantic. Số liệu thật do engine BRAVO tính (ADR-0005).
"""
from __future__ import annotations

import pathlib
from collections.abc import Mapping
from typing import TYPE_CHECKING

import yaml

from app.data_layer import money
from app.data_layer.semantic import MetricResult

if TYPE_CHECKING:
    from app.security.rls import Identity

_DEFAULT_FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "mock_financials_tt99.yaml"


class AccessDenied(PermissionError):
    """Người dùng không có quyền với chỉ tiêu nhạy (RLS ở tầng số)."""


class NoDemoData(ValueError):
    """Không có dữ liệu DEMO cho metric/kỳ này -> caller ABSTAIN."""


def _allowed(identity: "Identity", dept: str | None) -> bool:
    if getattr(identity, "is_admin", False):
        return True
    if "metric:read:all" in getattr(identity, "permissions", frozenset()):
        return True
    return dept in (getattr(identity, "department_ids", None) or [])


class MockDataSource:
    """DataSource demo (đọc YAML). Tôn trọng Protocol semantic.DataSource."""

    def __init__(self, path: pathlib.Path | None = None) -> None:
        data = yaml.safe_load((path or _DEFAULT_FIXTURE).read_text(encoding="utf-8"))
        self._meta: dict = data.get("meta", {})
        self._metrics: dict = data.get("metrics", {})

    def fetch(self, metric_id: str, params: Mapping[str, object],
              identity: "Identity") -> MetricResult:
        m = self._metrics.get(metric_id)
        if m is None:
            raise NoDemoData(f"Không có dữ liệu DEMO cho chỉ tiêu: {metric_id}")

        # RLS tầng số: chỉ tiêu nhạy -> chỉ phòng có quyền.
        if m.get("sensitive", False) and not _allowed(identity, m.get("dept")):
            raise AccessDenied(
                f"Bạn không có quyền xem chỉ tiêu nhạy '{metric_id}' (thuộc {m.get('dept')})."
            )

        ky = str(params.get("ky")) if params.get("ky") is not None else None
        by_period = m.get("by_period", {})
        if ky not in by_period:
            raise NoDemoData(f"Không có dữ liệu DEMO kỳ '{ky}' cho '{metric_id}'.")

        entity = self._meta.get("entity")
        return MetricResult(
            metric_id=metric_id,
            value=money.D(by_period[ky]),
            provenance=f"mock:{metric_id} ky={ky} entity={entity}",
            unit="VND",
            scale=m.get("scale"),
            currency="VND",
            period=ky,
            entity=entity,
            variant=m.get("variant"),
            is_demo=True,
        )
