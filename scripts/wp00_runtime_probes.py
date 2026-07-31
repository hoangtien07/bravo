#!/usr/bin/env python3
"""Run redaction-safe WP-00 cross-scope probes against an isolated Compose stack.

The probe data is synthetic and deterministic for a supplied run id.  It creates one document
for department A, one for department B, and one global document.  Results report only counts,
booleans and identifiers; passwords, DSNs, bearer tokens and document text are never printed or
written to the evidence file.

Run ``seed`` through a one-shot migrator/owner container, then run ``api`` inside the API service
(where native RLS is armed), and ``worker`` inside the worker service.  The runtime probes never
use the owner connection.  Example commands live in deploy/WP-00-RUNTIME-CUTOVER.md.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import secrets
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# The Docker image invokes this file directly (``python scripts/...``), which otherwise places
# only /app/scripts on sys.path.  Keep the repository package importable without relying on an
# operator-set PYTHONPATH.
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))


NAMESPACE = uuid.UUID("f0bafd4f-1c67-4a5d-81c7-d6f7e77c8f24")
MARKERS = {
    "a": "WP00_SCOPE_A_ONLY",
    "b": "WP00_SCOPE_B_ONLY",
    "global": "WP00_SCOPE_GLOBAL",
}


class ProbeError(RuntimeError):
    pass


def _id(run_id: str, name: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{run_id}:{name}")


def _dsn(name: str = "DATABASE_URL") -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ProbeError(f"{name} is required")
    return value.replace("postgresql+asyncpg://", "postgresql://", 1)


def _report(*, run_id: str, mode: str, checks: dict[str, bool], details: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "bravo-wp00-runtime-probe/v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "mode": mode,
        "synthetic_only": True,
        "checks": checks,
        "details": details,
        "passed": all(checks.values()),
    }


def _write_report(report: dict[str, Any], out: str | None) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if out:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    # Keep console output redaction-safe and compact for operator logs.
    status = "passed" if report["passed"] else "failed"
    print(f"WP-00 {report['mode']} scope probe {status}; run_id={report['run_id']}")


async def _embedding_literal(connection: Any) -> str:
    dim = await connection.fetchval(
        "SELECT (regexp_match(format_type(atttypid, atttypmod), '\\((\\d+)\\)'))[1]::int "
        "FROM pg_attribute WHERE attrelid = 'public.chunks'::regclass AND attname = 'embedding'"
    )
    if int(dim or 0) != 1536:
        raise ProbeError(f"expected EMBEDDING_DIM=1536, found {dim!r}")
    return "[" + ",".join(["0"] * int(dim)) + "]"


async def seed(run_id: str, owner_database_env: str) -> dict[str, Any]:
    import asyncpg
    from app.security.auth import hash_token
    from app.security.passwords import hash_password

    dept_a, dept_b = _id(run_id, "dept-a"), _id(run_id, "dept-b")
    employee_a = _id(run_id, "employee-a")
    source_a, source_b, source_global = (_id(run_id, "source-a"), _id(run_id, "source-b"),
                                          _id(run_id, "source-global"))
    chunk_a, chunk_b, chunk_global = (_id(run_id, "chunk-a"), _id(run_id, "chunk-b"),
                                      _id(run_id, "chunk-global"))
    mcp_token = f"wp00-synthetic-mcp-{run_id}"
    conn = await asyncpg.connect(_dsn(owner_database_env))
    try:
        vector = await _embedding_literal(conn)
        await conn.execute(
            "INSERT INTO departments (id, name, sensitive) VALUES ($1, $2, false), ($3, $4, false) "
            "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name",
            dept_a, f"WP00-A-{run_id}", dept_b, f"WP00-B-{run_id}")
        await conn.execute(
            "INSERT INTO employees (id, email, full_name, password_hash, is_admin, permissions, mcp_token_hash) "
            "VALUES ($1, $2, $3, $4, false, $5::varchar[], $6) "
            "ON CONFLICT (id) DO UPDATE SET password_hash = EXCLUDED.password_hash, "
            "permissions = EXCLUDED.permissions, mcp_token_hash = EXCLUDED.mcp_token_hash",
            employee_a, f"wp00-a-{run_id}@invalid.example", "WP-00 synthetic A",
            hash_password(secrets.token_urlsafe(32)),
            ["doc:read:own_dept"], hash_token(mcp_token))
        await conn.execute(
            "INSERT INTO employee_departments (employee_id, department_id) VALUES ($1, $2) "
            "ON CONFLICT DO NOTHING", employee_a, dept_a)
        await conn.execute(
            "INSERT INTO sources (id, filename, status, visibility) VALUES "
            "($1, $2, 'ready', 'department'), ($3, $4, 'ready', 'department'), "
            "($5, $6, 'ready', 'global') "
            "ON CONFLICT (id) DO UPDATE SET status = 'ready', visibility = EXCLUDED.visibility",
            source_a, f"wp00-a-{run_id}.txt", source_b, f"wp00-b-{run_id}.txt",
            source_global, f"wp00-global-{run_id}.txt")
        await conn.execute(
            "INSERT INTO source_departments (source_id, department_id) VALUES ($1, $2), ($3, $4) "
            "ON CONFLICT DO NOTHING", source_a, dept_a, source_b, dept_b)
        await conn.execute(
            "INSERT INTO chunks (id, source_id, content, embedding, is_table, extra, department_ids, visibility, owner_id) "
            "VALUES ($1, $2, $3, CAST($4 AS vector), false, '{}'::jsonb, $5::uuid[], $6, NULL), "
            "($7, $8, $9, CAST($4 AS vector), false, '{}'::jsonb, $10::uuid[], $6, NULL), "
            "($11, $12, $13, CAST($4 AS vector), false, '{}'::jsonb, ARRAY[]::uuid[], 'global', NULL) "
            "ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content, embedding = EXCLUDED.embedding, "
            "department_ids = EXCLUDED.department_ids, visibility = EXCLUDED.visibility",
            chunk_a, source_a, MARKERS["a"], vector, [dept_a], "department",
            chunk_b, source_b, MARKERS["b"], [dept_b],
            chunk_global, source_global, MARKERS["global"])
    finally:
        await conn.close()
    return _report(run_id=run_id, mode="seed", checks={"synthetic_rows_created": True,
                                                         "embedding_dim_1536": True},
                   details={"department_count": 2, "chunk_count": 3})


async def api_probe(run_id: str, base_url: str) -> dict[str, Any]:
    import httpx
    from app.mcp.server import kb_search
    from app.security.auth import create_access_token

    employee_a = _id(run_id, "employee-a")
    mcp_token = f"wp00-synthetic-mcp-{run_id}"
    source_a, source_b, source_global = (_id(run_id, "source-a"), _id(run_id, "source-b"),
                                          _id(run_id, "source-global"))
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {create_access_token(employee_a)}"}
        sources = await client.get(f"{base_url.rstrip('/')}/api/sources", headers=headers, timeout=30)
        if sources.status_code != 200:
            raise ProbeError(f"HTTP source listing returned {sources.status_code}")
        source_ids = {item.get("id") for item in sources.json()}
        answer = await client.post(f"{base_url.rstrip('/')}/api/ask", headers=headers,
                                   json={"question": "Trong các tài liệu được phép, hãy liệt kê chính xác "
                                                     "các marker WP00_SCOPE xuất hiện trong ngữ cảnh."}, timeout=120)
        if answer.status_code != 200:
            raise ProbeError(f"HTTP grounded ask returned {answer.status_code}")
        answer_json = answer.json()

    mcp_output = await kb_search(mcp_token, "WP00_SCOPE")
    http_scope = {str(source_a), str(source_global)}.issubset(source_ids) and str(source_b) not in source_ids
    answer_text = str(answer_json.get("answer", ""))
    answer_citations = {str(item.get("source_id")) for item in answer_json.get("citations", [])}
    checks = {
        "http_a_and_global_visible": http_scope,
        "http_b_not_visible": MARKERS["b"] not in answer_text and str(source_b) not in answer_citations,
        "mcp_a_and_global_visible": MARKERS["a"] in mcp_output and MARKERS["global"] in mcp_output,
        "mcp_b_not_visible": MARKERS["b"] not in mcp_output,
    }
    return _report(run_id=run_id, mode="api", checks=checks,
                   details={"http_visible_source_count": len(source_ids),
                            "http_citation_count": len(answer_citations),
                            "http_answer_grounded": bool(answer_json.get("grounded")),
                            "mcp_response_sha256": hashlib.sha256(mcp_output.encode()).hexdigest()})


async def worker_probe(run_id: str) -> dict[str, Any]:
    import asyncpg

    dept_a = _id(run_id, "dept-a")
    employee_a = _id(run_id, "employee-a")
    conn = await asyncpg.connect(_dsn())
    try:
        role = await conn.fetchrow("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        await conn.execute("SELECT set_config('bravo.employee_id', $1, false)", str(employee_a))
        await conn.execute("SELECT set_config('bravo.dept_ids', $1, false)", str(dept_a))
        await conn.execute("SELECT set_config('bravo.doc_read_level', 'own_dept', false)")
        visible = {
            row["content"]
            for row in await conn.fetch("SELECT content FROM chunks WHERE content LIKE 'WP00_SCOPE_%'")
        }
    finally:
        await conn.close()
    checks = {
        "worker_non_superuser": role is not None and not bool(role["rolsuper"]),
        "worker_no_bypassrls": role is not None and not bool(role["rolbypassrls"]),
        "worker_a_and_global_visible": {MARKERS["a"], MARKERS["global"]}.issubset(visible),
        "worker_b_not_visible": MARKERS["b"] not in visible,
    }
    return _report(run_id=run_id, mode="worker", checks=checks,
                   details={"worker_visible_marker_count": len(visible)})


async def main_async(args: argparse.Namespace) -> dict[str, Any]:
    if args.mode == "seed":
        return await seed(args.run_id, args.owner_database_env)
    if args.mode == "api":
        return await api_probe(args.run_id, args.api_base_url)
    if args.mode == "worker":
        return await worker_probe(args.run_id)
    raise ProbeError(f"unsupported mode: {args.mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="Non-secret UUID or operator run label.")
    parser.add_argument("--mode", choices=("seed", "api", "worker"), required=True)
    parser.add_argument("--api-base-url", default="http://api:8000")
    parser.add_argument("--owner-database-env", default="WP00_OWNER_DATABASE_URL",
                        help="Environment variable holding the owner/migrator DSN; seed mode only.")
    parser.add_argument("--out", help="Redaction-safe JSON evidence path.")
    args = parser.parse_args()
    try:
        report = asyncio.run(main_async(args))
    except (ProbeError, OSError, ValueError) as exc:
        print(f"WP-00 runtime probe failed: {exc}", file=sys.stderr)
        return 2
    _write_report(report, args.out)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
