"""A/B/C0 side-by-side comparison runner (plan P1 / stop-rule support).

Drives the same questions through multiple StepLoop arms and emits their answers side by side so a
reviewer (or a later blind SME pass) can judge them. The arms:

  A  — legacy chat            (AgentSession, consultant_mode='off')
  B  — current Consultant     (AgentSession, consultant_mode='on')
  C0 — bare model + evidence  (C0Arm)  ← the floor the V2 core must beat

`compare_arms` is transport-agnostic and takes ready StepLoop objects, so it is unit-testable with
fakes; `build_local_arms` wires the real arms against a DB session + identity. This is an evaluation
tool, not a product path.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol

from app.utils.yaml_compat import safe_load_file


class StepLoop(Protocol):
    async def step(self, user_message: str) -> dict: ...


async def _run_one(name: str, arm: StepLoop, question: str) -> dict[str, Any]:
    started = perf_counter()
    try:
        out = await arm.step(question)
        elapsed = round((perf_counter() - started) * 1000)
        return {"arm": name, "answer": out.get("answer", ""),
                "grounded": bool(out.get("grounded")),
                "citations": list(out.get("citations", []) or []),
                "routed_cloud": bool(out.get("routed_cloud", False)), "latency_ms": elapsed}
    except Exception as exc:  # one arm failing must not sink the comparison
        return {"arm": name, "error": f"{type(exc).__name__}: {exc}",
                "latency_ms": round((perf_counter() - started) * 1000)}


async def compare_arms(arm_factories: dict[str, Any], questions: list[str]) -> dict[str, Any]:
    """arm_factories: name -> zero-arg callable returning a FRESH StepLoop per question (so each
    case gets an isolated session). Runs arms sequentially per question (shared model rate limits)."""
    rows: list[dict[str, Any]] = []
    for q in questions:
        results = []
        for name, make in arm_factories.items():
            results.append(await _run_one(name, make(), q))
        rows.append({"question": q, "results": results})
    return {"n_questions": len(questions), "arms": list(arm_factories.keys()), "rows": rows}


def build_local_arms(db, identity) -> dict[str, Any]:
    """Wire the real A/B/C0 arms against a live DB session + identity (in-process, no HTTP)."""
    from app.agent.loop import AgentSession
    from app.eval.c0_arm import C0Arm

    def _legacy():
        s = AgentSession(db, identity, session_id=uuid.uuid4())
        s.consultant_mode = "off"
        return s

    def _consultant():
        s = AgentSession(db, identity, session_id=uuid.uuid4())
        s.consultant_mode = "on"
        return s

    return {"A_legacy": _legacy, "B_consultant": _consultant,
            "C0_bare": lambda: C0Arm(db, identity)}


def _questions_from_fixture(path: str | Path) -> list[str]:
    raw = safe_load_file(Path(path)) or {}
    out: list[str] = []
    for case in raw.get("cases", []):
        turns = case.get("turns") or []
        if turns:
            out.append(str(turns[0]["user"]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", default="app/eval/consultant_benchmark.example.yaml")
    parser.add_argument("--username", required=True)
    parser.add_argument("--max-questions", type=int)
    parser.add_argument("--out")
    args = parser.parse_args()

    async def run() -> dict[str, Any]:
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import NullPool

        from app.config import get_settings
        from app.database.models import Employee
        from app.security.auth import _employee_to_identity

        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        questions = _questions_from_fixture(args.fixture)[:args.max_questions]
        try:
            async with factory() as db:
                emp = (await db.execute(select(Employee).where(
                    Employee.email == args.username))).scalar_one()
                identity = await _employee_to_identity(emp)
                return await compare_arms(build_local_arms(db, identity), questions)
        finally:
            await engine.dispose()

    report = asyncio.run(run())
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
