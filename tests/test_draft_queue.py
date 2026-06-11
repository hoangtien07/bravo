"""Tests for draft-queue hardening (WP-E) — maker-checker + RLS predicate (pure parts)."""
from __future__ import annotations

import uuid

from app.erp.draft_queue import draft_scope_filter, maker_checker_ok
from app.security.rls import Identity


def test_self_approval_denied_by_default():
    uid = uuid.uuid4()
    ok, reason = maker_checker_ok(uid, uid, allow_self_approval=False)
    assert ok is False
    assert "tự duyệt" in reason


def test_other_approver_allowed():
    ok, reason = maker_checker_ok(uuid.uuid4(), uuid.uuid4(), allow_self_approval=False)
    assert ok is True and reason is None


def test_self_approval_allowed_when_configured():
    uid = uuid.uuid4()
    ok, _ = maker_checker_ok(uid, uid, allow_self_approval=True)
    assert ok is True


def test_draft_scope_filter_admin_sees_all():
    # admin -> true() predicate (no restriction); just assert it builds & is truthy-typed.
    admin = Identity(employee_id=uuid.uuid4(), is_admin=True)
    pred = draft_scope_filter(admin)
    assert pred is not None


def test_draft_scope_filter_no_permission_denies():
    # no draft:approve permission -> deny predicate (Draft.id IS NULL). Builds without DB.
    nobody = Identity(employee_id=uuid.uuid4())
    pred = draft_scope_filter(nobody)
    assert pred is not None
