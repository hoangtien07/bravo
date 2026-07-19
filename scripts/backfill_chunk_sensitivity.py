"""Backfill chunk `extra.is_sensitive` using the SAME deterministic classifier as ingestion.

Why: the retriever fail-closes any chunk whose `extra.is_sensitive` is missing to sensitive
(app/rag/retriever.py), which SKIPS the cloud/LLM reranker for the whole query
("llm_rerank skipped: N/N candidates sensitive/unknown"). Chunks ingested by an older path
left `is_sensitive` unset -> the single biggest retrieval-quality lever (rerank) was silently
dead across ~95% of the corpus.

This does NOT blanket-set false: it recomputes each source's sensitivity via
`app.security.sensitivity.ingest_sensitive` (knowledge_type + department scope), so a genuinely
sensitive source (payroll/HR/PII knowledge_type, or a chunk scoped to a sensitive department)
stays sensitive. Idempotent; only touches chunks where is_sensitive is currently unset.

Run:  .venv/bin/python scripts/backfill_chunk_sensitivity.py [--apply]   (default = dry-run)
"""
from __future__ import annotations

import argparse
import asyncio
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://bravo:bravo@localhost:5432/bravo")

from sqlalchemy import text  # noqa: E402

from app.database import async_session_factory  # noqa: E402
from app.security.sensitivity import ingest_sensitive  # noqa: E402


async def main(apply: bool) -> None:
    async with async_session_factory() as db:
        sensitive_dept = {
            r[0] for r in (await db.execute(
                text("select id from departments where sensitive = true"))).all()
        }
        sources = (await db.execute(text(
            "select s.id, s.knowledge_type, "
            "  coalesce(array_agg(sd.department_id) filter (where sd.department_id is not null), '{}') "
            "from sources s left join source_departments sd on sd.source_id = s.id "
            "group by s.id, s.knowledge_type"))).all()

        planned: dict[bool, int] = {True: 0, False: 0}
        for sid, kt, dept_ids in sources:
            depts = [d for d in (dept_ids or []) if d is not None]
            is_sensitive = ingest_sensitive(
                kt, has_departments=bool(depts),
                touches_sensitive_dept=any(d in sensitive_dept for d in depts))
            n = (await db.execute(text(
                "select count(*) from chunks where source_id = :sid "
                "and (extra->>'is_sensitive') is null"), {"sid": sid})).scalar_one()
            if not n:
                continue
            planned[is_sensitive] += n
            if apply:
                await db.execute(text(
                    "update chunks set extra = jsonb_set(coalesce(extra, cast('{}' as jsonb)), "
                    "'{is_sensitive}', cast(:val as jsonb), true) "
                    "where source_id = :sid and (extra->>'is_sensitive') is null"),
                    {"sid": sid, "val": "true" if is_sensitive else "false"})
        if apply:
            await db.commit()
        verb = "UPDATED" if apply else "WOULD SET (dry-run; pass --apply)"
        print(f"{verb}: is_sensitive=false -> {planned[False]} chunks, "
              f"is_sensitive=true -> {planned[True]} chunks")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args()
    asyncio.run(main(args.apply))
