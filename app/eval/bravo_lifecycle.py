"""BRAVO lifecycle retrieval eval.

This gate checks whether RAG retrieves the right *kind* of BRAVO source, not just any
semantically similar chunk. It uses `Chunk.extra` metadata written from
`file_system/bravo_corpus_manifest.yaml`.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from app.utils.yaml_compat import safe_load_file


@dataclass
class BravoLifecycleItem:
    id: str
    question: str
    actor_email: str
    expected_source_types: list[str] = field(default_factory=list)
    expected_modules: list[str] = field(default_factory=list)
    expected_labels: list[str] = field(default_factory=list)
    expected_behavior: str = "answer"  # answer | abstain | clarify (reported, not generated here)


@dataclass
class BravoLifecycleResult:
    item: BravoLifecycleItem
    retrieved: int
    source_type_hit: bool
    module_hit: bool
    label_hit: bool
    top_source_types: list[str]
    top_modules: list[str]

    @property
    def passed(self) -> bool:
        return self.source_type_hit and self.module_hit and self.label_hit


def _norm(v: str | None) -> str:
    return (v or "").strip().lower()


def _norm_set(values: Iterable[str]) -> set[str]:
    return {_norm(v) for v in values if _norm(v)}


def _meta_value(chunk: object, key: str) -> str:
    extra = getattr(chunk, "extra", None) or {}
    return str(extra.get(key) or "")


def _labels_hit(expected: set[str], labels: dict[str, str], chunks: list[object]) -> bool:
    if not expected:
        return True
    for c in chunks:
        label = labels.get(str(getattr(c, "source_id", "")), "")
        low = _norm(label)
        if any(exp in low for exp in expected):
            return True
    return False


def score_item(
    item: BravoLifecycleItem,
    chunks: list[object],
    *,
    source_labels: dict[str, str] | None = None,
) -> BravoLifecycleResult:
    """Score a retrieved chunk list against expected BRAVO metadata."""
    source_labels = source_labels or {}
    expected_types = _norm_set(item.expected_source_types)
    expected_modules = _norm_set(item.expected_modules)
    expected_labels = _norm_set(item.expected_labels)

    got_types = [_norm(_meta_value(c, "source_type")) for c in chunks]
    got_modules = [_norm(_meta_value(c, "module")) for c in chunks]

    source_type_hit = not expected_types or any(t in expected_types for t in got_types)
    module_hit = not expected_modules or any(m in expected_modules for m in got_modules)
    label_hit = _labels_hit(expected_labels, source_labels, chunks)

    return BravoLifecycleResult(
        item=item,
        retrieved=len(chunks),
        source_type_hit=source_type_hit,
        module_hit=module_hit,
        label_hit=label_hit,
        top_source_types=[t for t in got_types if t],
        top_modules=[m for m in got_modules if m],
    )


def summarize(results: list[BravoLifecycleResult]) -> dict[str, float]:
    n = len(results) or 1
    return {
        "n": float(len(results)),
        "pass_rate": sum(r.passed for r in results) / n,
        "source_type_accuracy": sum(r.source_type_hit for r in results) / n,
        "module_accuracy": sum(r.module_hit for r in results) / n,
        "label_accuracy": sum(r.label_hit for r in results) / n,
    }


def load_items(path: str | Path) -> list[BravoLifecycleItem]:
    raw = safe_load_file(path) or []
    if not isinstance(raw, list):
        raise ValueError("BRAVO lifecycle golden set must be a YAML list")
    return [BravoLifecycleItem(**row) for row in raw]


async def _identity_for(db, email: str):
    from sqlalchemy import select

    from app.database.models import Employee
    from app.security.rls import Identity

    emp = (await db.execute(select(Employee).where(Employee.email == email))).scalar_one()
    return Identity(employee_id=emp.id, department_ids=list(emp.department_ids),
                    permissions=frozenset(emp.permissions or []), is_admin=emp.is_admin)


async def _source_labels(db, chunks: list[object]) -> dict[str, str]:
    from sqlalchemy import select

    from app.database.models import Source

    ids = {getattr(c, "source_id", None) for c in chunks}
    ids.discard(None)
    if not ids:
        return {}
    rows = (await db.execute(
        select(Source).where(Source.id.in_([uuid.UUID(str(x)) for x in ids]))
    )).scalars().all()
    return {str(s.id): f"{s.knowledge_type or ''} {s.filename or ''}" for s in rows}


async def run_items(items: list[BravoLifecycleItem], *, k: int = 8) -> list[BravoLifecycleResult]:
    from app.database import async_session_factory
    from app.rag import retriever
    from app.security.rls import Identity

    results: list[BravoLifecycleResult] = []
    async with async_session_factory() as db:
        identity_cache: dict[str, Identity] = {}
        for item in items:
            if item.actor_email not in identity_cache:
                identity_cache[item.actor_email] = await _identity_for(db, item.actor_email)
            ident = identity_cache[item.actor_email]
            chunks = await retriever.retrieve(db, ident, item.question, top_n=k)
            labels = await _source_labels(db, chunks)
            results.append(score_item(item, chunks, source_labels=labels))
    return results


async def main(
    path: str = "app/eval/golden_set_bravo_lifecycle.example.yaml",
    *,
    k: int = 8,
) -> int:
    items = load_items(path)
    results = await run_items(items, k=k)
    metrics = summarize(results)
    for r in results:
        mark = "✓" if r.passed else "✗"
        print(
            f"[{mark}] {r.item.id}: type={r.source_type_hit} "
            f"module={r.module_hit} label={r.label_hit}"
        )
    print("BRAVO lifecycle retrieval metrics:", metrics)
    return 0 if metrics["pass_rate"] >= 0.95 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
