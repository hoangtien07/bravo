"""WP-04 native-RLS backstop probe for durable AccountingCase metadata."""
from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import text

from app.security.native_rls import apply_rls_gucs
from app.security.rls import Identity
from tests.db_support import db_available


pytestmark = pytest.mark.skipif(not db_available(), reason="Postgres not reachable")


def _engine():
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    from app.config import get_settings
    return create_async_engine(get_settings().database_url, poolclass=NullPool)


def test_native_rls_hides_cross_department_accounting_cases_for_create_scoped_maker():
    async def run() -> None:
        engine = _engine()
        dept_a, dept_b = uuid.uuid4(), uuid.uuid4()
        owner_a, owner_b = uuid.uuid4(), uuid.uuid4()
        case_a, case_b = f"case_{uuid.uuid4().hex}", f"case_{uuid.uuid4().hex}"
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                await conn.execute(text(
                    "INSERT INTO departments (id, name, sensitive) VALUES "
                    "(:a, 'accounting-case-rls-a', false), (:b, 'accounting-case-rls-b', false)"),
                    {"a": dept_a, "b": dept_b})
                await conn.execute(text(
                    "INSERT INTO employees (id, email, full_name, password_hash, is_admin, permissions) VALUES "
                    "(:a, 'case-rls-a@example.invalid', 'A', 'x', false, ARRAY[]::varchar[]), "
                    "(:b, 'case-rls-b@example.invalid', 'B', 'x', false, ARRAY[]::varchar[])"),
                    {"a": owner_a, "b": owner_b})
                await conn.execute(text(
                    "INSERT INTO accounting_cases_v2 (case_id, case_type, owner_id, department_ids, scope, state) VALUES "
                    "(:ca, 'bank_reconciliation', :oa, ARRAY[:da]::uuid[], '{}'::jsonb, 'EVIDENCE_READY'), "
                    "(:cb, 'bank_reconciliation', :ob, ARRAY[:db]::uuid[], '{}'::jsonb, 'EVIDENCE_READY')"),
                    {"ca": case_a, "cb": case_b, "oa": owner_a, "ob": owner_b, "da": dept_a, "db": dept_b})
                await conn.execute(text("ALTER TABLE accounting_cases_v2 ENABLE ROW LEVEL SECURITY"))
                await conn.execute(text("ALTER TABLE accounting_cases_v2 FORCE ROW LEVEL SECURITY"))
                await conn.execute(text("CREATE ROLE accounting_case_rls_probe NOSUPERUSER"))
                await conn.execute(text("GRANT SELECT ON accounting_cases_v2 TO accounting_case_rls_probe"))
                maker = Identity(employee_id=owner_a, department_ids=[dept_a],
                                 permissions=frozenset({"accounting_case:create:own_dept"}))
                await apply_rls_gucs(conn, maker)
                await conn.execute(text("SET LOCAL ROLE accounting_case_rls_probe"))
                visible = set((await conn.execute(text(
                    "SELECT case_id FROM accounting_cases_v2 WHERE case_id = ANY(:ids)"),
                    {"ids": [case_a, case_b]})).scalars().all())
                await conn.execute(text("RESET ROLE"))
                assert visible == {case_a}
                await trans.rollback()
        finally:
            await engine.dispose()

    asyncio.run(run())
