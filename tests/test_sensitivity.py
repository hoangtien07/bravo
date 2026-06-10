"""Tests for egress sensitivity classification (WP-C / ADR-0011) — fail-closed to local."""
from __future__ import annotations

from app.security.sensitivity import classify_context


class _Item:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_sensitive_department_forces_local():
    item = _Item(department_ids=["ke_toan"])
    assert classify_context([item], sensitive_dept_ids={"ke_toan"}) is True


def test_sensitive_knowledge_type_forces_local():
    assert classify_context([_Item(department_ids=[], knowledge_type="payroll")]) is True


def test_non_sensitive_context_allows_cloud():
    item = _Item(department_ids=["kinh_doanh"], knowledge_type="guide")
    assert classify_context([item], sensitive_dept_ids={"ke_toan"}) is False


def test_empty_context_fails_closed_to_local():
    assert classify_context([]) is True


def test_real_financial_metric_sensitive_but_demo_mock_not():
    real = _Item(metric_id="dt", currency="VND", is_demo=False)
    demo = _Item(metric_id="dt", currency="VND", is_demo=True, department_ids=[])
    assert classify_context([real]) is True       # số thật -> local
    assert classify_context([demo]) is False      # mock DEMO -> cloud OK


def test_any_sensitive_item_taints_whole_context():
    ok = _Item(department_ids=["kinh_doanh"], knowledge_type="guide")
    bad = _Item(department_ids=["nhan_su"])
    assert classify_context([ok, bad], sensitive_dept_ids={"nhan_su"}) is True
