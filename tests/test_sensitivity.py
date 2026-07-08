"""Tests for egress sensitivity classification (WP-C / ADR-0011) — fail-closed to local."""
from __future__ import annotations

from app.security.sensitivity import classify_context, ingest_sensitive


class _Item:
    def __init__(self, **kw):
        self.__dict__.update(kw)


# --- ingest_sensitive (egress-guard khi NẠP, Phase 0.2) ---
def test_ingest_sensitive_knowledge_type_local():
    assert ingest_sensitive("payroll", has_departments=False,
                            touches_sensitive_dept=False) is True


def test_ingest_sensitive_department_local():
    assert ingest_sensitive("guide", has_departments=True,
                            touches_sensitive_dept=True) is True


def test_ingest_global_unlabeled_failclosed_local():
    # Vá lỗ: global (không phòng ban) + không knowledge_type -> NHẠY (local), không cloud-embed.
    assert ingest_sensitive("", has_departments=False, touches_sensitive_dept=False) is True
    assert ingest_sensitive(None, has_departments=False, touches_sensitive_dept=False) is True


def test_ingest_public_guide_allows_cloud():
    # Tài liệu công khai có knowledge_type hợp lệ -> KHÔNG nhạy -> cloud OK (demo không đổi).
    assert ingest_sensitive("guide", has_departments=False,
                            touches_sensitive_dept=False) is False
    assert ingest_sensitive("userguide", has_departments=True,
                            touches_sensitive_dept=False) is False


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
