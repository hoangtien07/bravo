"""Validation and read-only lookup for version-aware schema/KEDB evidence."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import KnownError, SchemaSnapshot


def schema_fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def validate_schema_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept metadata only: tables/fields/relations, no connection data or SQL scripts."""
    tables = payload.get("tables")
    if not isinstance(tables, list) or not tables:
        raise ValueError("schema snapshot requires a non-empty tables list")
    clean_tables: list[dict[str, Any]] = []
    for table in tables:
        if not isinstance(table, dict) or not isinstance(table.get("name"), str):
            raise ValueError("each table needs a name")
        fields = table.get("fields", [])
        if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
            raise ValueError("table fields must be string names")
        clean_tables.append({"name": table["name"][:200], "fields": [field[:200] for field in fields],
                             "relations": table.get("relations", []) if isinstance(table.get("relations", []), list) else []})
    return {"tables": clean_tables}


async def lookup_schema(db: AsyncSession, query: str, *, bravo_version: str | None = None,
                        environment: str | None = None) -> list[dict[str, Any]]:
    stmt = select(SchemaSnapshot).where(SchemaSnapshot.status == "verified")
    if bravo_version:
        stmt = stmt.where(SchemaSnapshot.bravo_version == bravo_version)
    if environment:
        stmt = stmt.where(SchemaSnapshot.environment == environment)
    rows = list((await db.execute(stmt.order_by(SchemaSnapshot.created_at.desc()).limit(20))).scalars())
    tokens = [token.casefold() for token in query.split() if len(token) >= 2]
    facts: list[dict[str, Any]] = []
    for snapshot in rows:
        for table in snapshot.payload.get("tables", []):
            haystack = " ".join([table.get("name", ""), *table.get("fields", [])]).casefold()
            if not tokens or any(token in haystack for token in tokens):
                facts.append({"table": table.get("name"), "fields": table.get("fields", []),
                              "relations": table.get("relations", []), "bravo_version": snapshot.bravo_version,
                              "environment": snapshot.environment, "snapshot_id": str(snapshot.id),
                              "source_ref": snapshot.source_ref})
    return facts[:20]


async def search_kedb(db: AsyncSession, query: str, *, bravo_version: str | None = None,
                      environment: str | None = None) -> list[KnownError]:
    # Match meaningful query tokens independently: an incident report usually inserts extra
    # words between symptom terms, so a single `%whole sentence%` predicate misses the same issue.
    tokens = [token for token in query.split() if len(token) >= 2][:8]
    text_conditions = [or_(KnownError.title.ilike(f"%{token}%"),
                           KnownError.symptom.ilike(f"%{token}%"),
                           KnownError.probable_cause.ilike(f"%{token}%"))
                       for token in tokens]
    stmt = select(KnownError).where(
        KnownError.status == "verified",
        and_(*text_conditions) if text_conditions else True,
    )
    if bravo_version:
        stmt = stmt.where(or_(KnownError.bravo_version == bravo_version, KnownError.bravo_version.is_(None)))
    if environment:
        stmt = stmt.where(or_(KnownError.environment == environment, KnownError.environment.is_(None)))
    return list((await db.execute(stmt.order_by(KnownError.created_at.desc()).limit(20))).scalars())
