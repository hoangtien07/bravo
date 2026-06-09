"""Row-Level Security engine.

THE crown jewel (rewritten from arkon PATTERNS — not copied; PolyForm, ADR-0008).

Invariant #1 (CLAUDE.md): scope filtering happens INSIDE the SQL query (predicate
pushdown), never in application memory. Findings/J: in-query gating = 0% leakage;
post-retrieval filtering collapses recall at scale.

Scope rule (SECURITY-RLS §2): a resource with ZERO departments is GLOBAL. Otherwise
it is visible to members of ANY of its departments (OR scope). Admin bypasses.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # heavy imports kept out of module top so pure logic is dep-free/testable
    from sqlalchemy import ColumnElement


@dataclass(frozen=True)
class Identity:
    """The resolved requester. Carried on every request; drives RLS."""

    employee_id: uuid.UUID
    department_ids: list[uuid.UUID] = field(default_factory=list)
    permissions: frozenset[str] = field(default_factory=frozenset)
    is_admin: bool = False

    def scope_level(self, resource: str, action: str) -> str | None:
        """Return 'all' | 'own_dept' | None for a {resource}:{action} permission."""
        if self.is_admin:
            return "all"
        if f"{resource}:{action}:all" in self.permissions:
            return "all"
        if f"{resource}:{action}:own_dept" in self.permissions:
            return "own_dept"
        return None


def chunk_scope_filter(identity: Identity, action: str = "read") -> "ColumnElement[bool]":
    """SQL predicate restricting Chunk rows to what `identity` may access.

    Apply directly in the vector-search query's WHERE clause (RLS-on-vector):

        stmt = select(Chunk).where(chunk_scope_filter(identity)).order_by(
            Chunk.embedding.cosine_distance(query_vec)
        ).limit(k)

    - Admin / `doc:read:all`  -> no restriction.
    - `doc:read:own_dept`     -> chunk is global (empty department_ids) OR overlaps user depts.
    - No permission           -> deny all.
    """
    from sqlalchemy import or_, true
    from sqlalchemy.dialects.postgresql import array

    from app.database.models import Chunk

    level = identity.scope_level("doc", action)
    if level == "all":
        return true()
    if level is None:
        # Deny everything (false predicate).
        return Chunk.id.is_(None)

    # own_dept: global rows (empty array) OR array overlap with user's departments.
    is_global = Chunk.department_ids == []  # noqa: E711 — array-empty check in SQL
    if not identity.department_ids:
        return is_global
    overlaps = Chunk.department_ids.op("&&")(array(identity.department_ids, type_=Chunk.department_ids.type.item_type))
    return or_(is_global, overlaps)


def source_scope_filter(identity: Identity, action: str = "read") -> "ColumnElement[bool]":
    """SQL predicate restricting Source rows (list endpoints). Same rule as chunks:
    a source with NO rows in source_departments is GLOBAL; else OR-overlap with depts.
    Enforced IN the query (no post-filter)."""
    from sqlalchemy import exists, or_, select, true

    from app.database.models import Source, SourceDepartment

    level = identity.scope_level("doc", action)
    if level == "all":
        return true()
    if level is None:
        return Source.id.is_(None)

    has_any_dept = exists(
        select(SourceDepartment.source_id).where(SourceDepartment.source_id == Source.id)
    )
    is_global = ~has_any_dept
    if not identity.department_ids:
        return is_global
    in_my_dept = exists(
        select(SourceDepartment.source_id).where(
            (SourceDepartment.source_id == Source.id)
            & (SourceDepartment.department_id.in_(identity.department_ids))
        )
    )
    return or_(is_global, in_my_dept)


def can_access_source_departments(identity: Identity, source_department_ids: list[uuid.UUID],
                                  action: str = "read") -> bool:
    """In-memory check for a single already-loaded source (detail endpoints).

    Mirror of the SQL predicate above for the single-object case. List endpoints must
    still filter in SQL via chunk_scope_filter / an equivalent source filter.
    """
    level = identity.scope_level("doc", action)
    if level == "all":
        return True
    if level is None:
        return False
    if not source_department_ids:  # global
        return True
    return bool(set(source_department_ids) & set(identity.department_ids))


def out_of_scope_hint(scope_counts: dict[str, int]) -> str | None:
    """Render an out-of-scope hint (SECURITY-RLS §4): expose ONLY scope label + count,
    NEVER titles/content. `scope_counts` maps a human label -> number of hidden items.
    """
    if not scope_counts:
        return None
    lines = [f"- {n} mục thuộc {label} — liên hệ quản trị để xin quyền."
             for label, n in scope_counts.items() if n > 0]
    return ("Có kết quả ngoài phạm vi quyền của bạn:\n" + "\n".join(lines)) if lines else None
