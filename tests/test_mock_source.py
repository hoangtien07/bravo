"""Tests for MockDataSource (WP-F) — value-object + RLS tầng số + ABSTAIN."""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from app.data_layer import catalog, semantic
from app.data_layer.mock_source import AccessDenied, MockDataSource, NoDemoData
from app.data_layer.semantic import MetricQuery
from app.security.rls import Identity

catalog.register_catalog()  # nạp whitelist metric (có scope_columns)

_KETOAN = Identity(employee_id=uuid.uuid4(), department_ids=["ke_toan"])
_KINHDOANH = Identity(employee_id=uuid.uuid4(), department_ids=["kinh_doanh"])
_NHANSU = Identity(employee_id=uuid.uuid4(), department_ids=["nhan_su"])
_GIAMDOC = Identity(employee_id=uuid.uuid4(), is_admin=True)


def test_fetch_returns_value_object_with_scale():
    src = MockDataSource()
    r = src.fetch("doanh_thu_thuan", {"ky": "2026-Q2", "don_vi": "ThépDEMO"}, _KETOAN)
    assert r.value == Decimal("52.8")
    assert r.scale == "tỷ"
    assert r.is_demo is True
    assert r.base_value() == Decimal("52800000000")  # 52.8 tỷ quy về đồng
    assert "doanh_thu_thuan" in r.provenance


def test_sensitive_metric_denied_for_wrong_department():
    src = MockDataSource()
    with pytest.raises(AccessDenied):
        src.fetch("quy_luong_thang", {"ky": "2026-01", "don_vi": "x"}, _KINHDOANH)


def test_sensitive_metric_allowed_for_owner_and_admin():
    src = MockDataSource()
    assert src.fetch("quy_luong_thang", {"ky": "2026-01", "don_vi": "x"}, _NHANSU).value == Decimal("3.4")
    assert src.fetch("quy_luong_thang", {"ky": "2026-01", "don_vi": "x"}, _GIAMDOC).value == Decimal("3.4")


def test_sensitive_metric_allowed_via_permission_for_real_uuid_identity():
    """Identity THẬT (department_ids là UUID) được cấp 'metric:read:hr' -> xem được lương.
    Identity UUID KHÔNG có permission -> bị chặn (dept-code không khớp UUID)."""
    src = MockDataSource()
    hr = Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                  permissions=frozenset({"metric:read:hr"}))
    assert src.fetch("quy_luong_thang", {"ky": "2026-01", "don_vi": "x"}, hr).value == Decimal("3.4")
    no = Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()])
    with pytest.raises(AccessDenied):
        src.fetch("quy_luong_thang", {"ky": "2026-01", "don_vi": "x"}, no)


def test_no_demo_data_period_abstains():
    src = MockDataSource()
    with pytest.raises(NoDemoData):
        src.fetch("doanh_thu_thuan", {"ky": "2099-Q9", "don_vi": "x"}, _KETOAN)


def test_execute_through_semantic_enforces_whitelist_and_rls():
    src = MockDataSource()
    # metric trong whitelist + có dữ liệu -> trả value-object
    r = semantic.execute(MetricQuery("gia_von_hang_ban", {"ky": "2026-Q2", "don_vi": "x"}), src, _KETOAN)
    assert r.value == Decimal("41.1") and r.scale == "tỷ"
    # metric ngoài whitelist -> ABSTAIN
    with pytest.raises(ValueError, match="ABSTAIN"):
        semantic.execute(MetricQuery("metric_bia_dat", {}), src, _KETOAN)
