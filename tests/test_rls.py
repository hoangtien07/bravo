"""Unit tests for the RLS scope logic (no DB needed) — the crown jewel.

Covers SECURITY-RLS §2: global resources, own_dept overlap, deny-by-default, admin.
"""
from __future__ import annotations

import uuid

from app.security.rls import Identity, can_access_source_departments, out_of_scope_hint

HR = uuid.uuid4()
ACCOUNTING = uuid.uuid4()


def _id(perms, depts=(), admin=False):
    return Identity(employee_id=uuid.uuid4(), department_ids=list(depts),
                    permissions=frozenset(perms), is_admin=admin)


def test_admin_sees_everything():
    admin = _id([], admin=True)
    assert can_access_source_departments(admin, [HR]) is True


def test_no_permission_denies():
    nobody = _id([])  # no doc:read:* permission
    assert can_access_source_departments(nobody, []) is False
    assert can_access_source_departments(nobody, [HR]) is False


def test_global_resource_visible_to_any_reader():
    viewer = _id(["doc:read:own_dept"], depts=[ACCOUNTING])
    assert can_access_source_departments(viewer, []) is True  # empty depts = global


def test_own_dept_overlap():
    acc = _id(["doc:read:own_dept"], depts=[ACCOUNTING])
    assert can_access_source_departments(acc, [ACCOUNTING]) is True
    assert can_access_source_departments(acc, [HR]) is False  # no overlap -> denied


def test_read_all_scope():
    km = _id(["doc:read:all"], depts=[])
    assert can_access_source_departments(km, [HR]) is True


def test_out_of_scope_hint_leaks_only_counts():
    hint = out_of_scope_hint({"phòng HR": 3})
    assert "3" in hint and "HR" in hint
    assert out_of_scope_hint({}) is None
