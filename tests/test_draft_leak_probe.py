"""Draft leak predicate (Phase 0.3) — draft phòng B không được lọt sang approver phòng A.

Lớp bất thường mà lỗ 'draft do agent tạo = NULL/global' từng gây (OWASP ASI03). Test PURE
(không cần DB) trên predicate `draft_leaked` + helper resolve scope."""
from __future__ import annotations

import uuid

from app.eval.probes import draft_leaked
from app.erp.draft_queue import resolve_draft_department
from app.security.rls import Identity

_DEPT_A = uuid.uuid4()
_DEPT_B = uuid.uuid4()


class _Draft:
    def __init__(self, department_id):
        self.id = uuid.uuid4()
        self.department_id = department_id


def _actor(depts, *, perms=frozenset({"draft:approve:own_dept"}), admin=False):
    return Identity(employee_id=uuid.uuid4(), department_ids=list(depts),
                    permissions=frozenset(perms), is_admin=admin)


def test_foreign_dept_draft_is_leak():
    actor = _actor([_DEPT_A])
    assert draft_leaked(_Draft(_DEPT_B), actor, _DEPT_B) is True


def test_own_dept_draft_not_leak():
    actor = _actor([_DEPT_A])
    assert draft_leaked(_Draft(_DEPT_A), actor, _DEPT_B) is False


def test_global_draft_not_leak():
    # department_id=None = dùng chung chủ ý -> không tính rò.
    actor = _actor([_DEPT_A])
    assert draft_leaked(_Draft(None), actor, _DEPT_B) is False


def test_admin_and_scope_all_never_leak():
    assert draft_leaked(_Draft(_DEPT_B), _actor([_DEPT_A], admin=True), _DEPT_B) is False
    alld = _actor([_DEPT_A], perms={"draft:approve:all"})
    assert draft_leaked(_Draft(_DEPT_B), alld, _DEPT_B) is False


# --- resolve_draft_department: fail-closed scope cho draft do agent tạo ---
def test_resolve_single_department():
    assert resolve_draft_department(_actor([_DEPT_A])) == _DEPT_A


def test_resolve_payload_foreign_department_is_rejected():
    got = resolve_draft_department(_actor([_DEPT_A]), {"department_id": str(_DEPT_B)})
    assert got is None


def test_resolve_payload_own_department_is_allowed():
    got = resolve_draft_department(_actor([_DEPT_A]), {"department_id": str(_DEPT_A)})
    assert got == _DEPT_A


def test_resolve_none_when_ambiguous():
    # 0 hoặc >1 phòng, không dept trong payload -> None -> caller fail-closed (không global).
    assert resolve_draft_department(_actor([])) is None
    assert resolve_draft_department(_actor([_DEPT_A, _DEPT_B])) is None
