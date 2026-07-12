"""Q4 — BravoGen parity benchmark harness.

Runs a fixed question set through the REAL AgentSession.step (prod retrieval config) and
records bravo's answer + grounding + citations for BLIND A/B grading against BravoGen
(LibreChat+Gemini). BravoGen answers are collected out-of-band and merged into the same
sheet; a human grader scores win/tie/loss with the rubric in docs/CORPUS-OPS.md.

Usage:
    python -m app.eval.parity_bench app/eval/parity_questions.yaml > parity_run.json

The output is JSON: one record per question with bravo_answer, grounded, citations, and an
empty `bravogen_answer`/`verdict` to fill in during grading. This harness does NOT call
BravoGen (no API) and does NOT self-grade (an LLM-judge is not a release gate — CONTRACTS §5).
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.loop import AgentSession
from app.database import async_session_factory
from app.database.models import Employee
from app.security.rls import Identity
from app.utils.yaml_compat import safe_load_file


async def _identity_for(db: AsyncSession, email: str | None) -> Identity:
    if email:
        emp = (await db.execute(
            select(Employee).where(Employee.email == email))).scalar_one_or_none()
        if emp is not None:
            return Identity(employee_id=emp.id, department_ids=list(emp.department_ids),
                            permissions=frozenset(emp.permissions or []), is_admin=emp.is_admin)
    # Fallback: a broad reader so retrieval isn't the variable under test.
    return Identity(employee_id=uuid.uuid4(), department_ids=[],
                    permissions=frozenset({"doc:read:all"}), is_admin=True)


async def run_parity(path: str) -> list[dict]:
    spec = safe_load_file(Path(path)) or {}
    questions = spec.get("questions") or []
    out: list[dict] = []
    async with async_session_factory() as db:
        for q in questions:
            text = q["question"] if isinstance(q, dict) else str(q)
            actor_email = q.get("actor_email") if isinstance(q, dict) else None
            group = q.get("group") if isinstance(q, dict) else None
            identity = await _identity_for(db, actor_email)
            session = AgentSession(db, identity, session_id=uuid.uuid4())
            try:
                res = await session.step(text)
            except Exception as exc:  # keep the batch running
                res = {"answer": f"[LỖI: {exc}]", "grounded": False, "citations": []}
            out.append({
                "group": group,
                "question": text,
                "bravo_answer": res.get("answer", ""),
                "grounded": res.get("grounded"),
                "routed_cloud": res.get("routed_cloud"),
                "citations": res.get("citations", []),
                # to be filled during blind grading:
                "bravogen_answer": "",
                "verdict": "",          # win | tie | loss (bravo vs bravogen)
                "failure_label": "",    # retrieval-miss | corpus-miss | synthesis-poor | wrong-task-type
            })
    return out


def main() -> int:
    import asyncio
    path = sys.argv[1] if len(sys.argv) > 1 else "app/eval/parity_questions.yaml"
    records = asyncio.run(run_parity(path))
    json.dump(records, sys.stdout, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
