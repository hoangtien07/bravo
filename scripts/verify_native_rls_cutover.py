#!/usr/bin/env python3
"""Read-only preflight for the native Postgres RLS cutover.

Run with the runtime application's DATABASE_URL, never an owner/migrator URL. It reads only
PostgreSQL catalogs and deliberately prints neither a DSN nor any secret.
"""
from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Mapping

import asyncpg


def _database_url() -> str:
    value = os.environ.get("DATABASE_URL", "")
    if not value:
        raise RuntimeError("DATABASE_URL is required (use the non-owner runtime role)")
    return value.replace("postgresql+asyncpg://", "postgresql://", 1)


def cutover_failures(role: Mapping[str, object], table: Mapping[str, object], has_policy: bool) -> list[str]:
    """Pure evaluation seam: keep the operator check testable without a live database."""
    failures: list[str] = []
    if role["rolsuper"]:
        failures.append("runtime role is SUPERUSER")
    if role["rolbypassrls"]:
        failures.append("runtime role has BYPASSRLS")
    if table["is_owner"]:
        failures.append("runtime role owns protected table chunks")
    if not table["relrowsecurity"]:
        failures.append("chunks does not have ROW LEVEL SECURITY enabled")
    if not table["relforcerowsecurity"]:
        failures.append("chunks does not have FORCE ROW LEVEL SECURITY enabled")
    if not has_policy:
        failures.append("chunks_rls_backstop SELECT policy is missing")
    if os.environ.get("NATIVE_RLS_ENABLED", "").lower() not in {"1", "true", "yes"}:
        failures.append("NATIVE_RLS_ENABLED is not enabled for the runtime")
    return failures


async def _check() -> list[str]:
    connection = await asyncpg.connect(_database_url())
    try:
        role = await connection.fetchrow(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        table = await connection.fetchrow(
            "SELECT relrowsecurity, relforcerowsecurity, "
            "relowner = (SELECT oid FROM pg_roles WHERE rolname = current_user) AS is_owner "
            "FROM pg_class WHERE oid = 'public.chunks'::regclass")
        has_policy = await connection.fetchval(
            "SELECT EXISTS (SELECT 1 FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = 'chunks' "
            "AND policyname = 'chunks_rls_backstop' AND cmd = 'SELECT')")
    finally:
        await connection.close()
    if role is None or table is None:
        return ["cannot read the required PostgreSQL role/table catalogs"]
    return cutover_failures(role, table, bool(has_policy))


def main() -> int:
    try:
        failures = asyncio.run(_check())
    except Exception as exc:
        print(f"native-RLS cutover preflight could not run: {exc}", file=sys.stderr)
        return 2
    if failures:
        print("native-RLS cutover NOT ready:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("native-RLS cutover preflight passed (catalog-only check).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
