"""Eval CI runner.

Two entrypoints:
  * `python -m app.eval.run [golden_set.yaml]`  — legacy retrieval-only gate (citation/
    refusal/ACL-leak) using the single-turn schema.
  * `python -m app.eval.run --passk`            — WP-H pass^k trajectory gate: runs the
    golden trajectories k times through the REAL AgentSession.step (or a mock loop when
    `--mock`), computes pass^k + HARD-FAIL detectors, and exits non-zero on a gate failure
    (blocks merge). See app.eval.passk for the detectors and gate.

Retrieval-level metrics are deterministic (no LLM needed). Generator faithfulness (RAGAS)
is an optional extra step run with a LOCAL judge (app.eval.faithfulness).
"""
from __future__ import annotations

import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.database.models import Employee
from app.eval._compat import GoldenItem, ItemResult, summarize
from app.eval.probes import assert_no_leak
from app.rag import retriever
from app.security.rls import Identity

CITATION_THRESHOLD = 0.95
REFUSAL_THRESHOLD = 0.95


async def _identity_for(db: AsyncSession, email: str) -> Identity:
    emp = (await db.execute(select(Employee).where(Employee.email == email))).scalar_one()
    return Identity(employee_id=emp.id, department_ids=list(emp.department_ids),
                    permissions=frozenset(emp.permissions or []), is_admin=emp.is_admin)


async def run_golden(db: AsyncSession, items: list[GoldenItem]) -> list[ItemResult]:
    # Q4: run with the SAME retrieval config as prod (rerank per settings, top_n=12 like the
    # chat loop) so the gate certifies the shipped pipeline, not a divergent one (was
    # use_rerank=False / top_n=8 while prod runs LLM rerank at top_n=12).
    results: list[ItemResult] = []
    for it in items:
        actor = await _identity_for(db, it.actor_email)
        chunks = await retriever.retrieve(db, actor, it.question, top_n=12)
        results.append(ItemResult(
            item=it,
            refused=len(chunks) == 0,
            cited_source_ids=sorted({c.source_id for c in chunks}),
        ))
    return results


def _load_yaml(path: str) -> list[GoldenItem]:
    import yaml  # optional dep

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or []
    return [GoldenItem(**row) for row in raw]


async def main(path: str | None) -> int:
    async with async_session_factory() as db:
        items = _load_yaml(path) if path else []
        results = await run_golden(db, items) if items else []
        metrics = summarize(results) if results else {"citation_accuracy": 1.0, "refusal_accuracy": 1.0, "n": 0}
        print("Golden metrics:", metrics)

        # ACL leak gate — pick two scoped users that should NOT see each other's data.
        leaks: list = []
        ket = (await db.execute(select(Employee).where(Employee.email == "ketoan@bravo.vn"))).scalar_one_or_none()
        hr = (await db.execute(select(Employee).where(Employee.email == "nhansu@bravo.vn"))).scalar_one_or_none()
        if ket and hr and ket.department_ids and hr.department_ids:
            actor = Identity(employee_id=ket.id, department_ids=list(ket.department_ids),
                             permissions=frozenset(ket.permissions or []))
            leaks = await assert_no_leak(db, actor, foreign_dept=hr.department_ids[0],
                                         queries=["lương", "hợp đồng", "nhân sự", "doanh thu"])
        print(f"ACL leaks: {len(leaks)}")

        ok = (
            metrics["citation_accuracy"] >= CITATION_THRESHOLD
            and metrics["refusal_accuracy"] >= REFUSAL_THRESHOLD
            and not leaks
        )
        print("RESULT:", "PASS" if ok else "FAIL")
        return 0 if ok else 1


# --------------------------------------------------------------------------------------
# WP-H pass^k gate — runs golden TRAJECTORIES k times end-to-end.
# --------------------------------------------------------------------------------------
async def passk_main(*, use_mock: bool, k: int) -> int:
    """WP-H gate entrypoint. Returns process exit code (0 = pass, non-zero = block merge)."""
    from app.eval.passk import MockLoop, evaluate_gate, run_passk
    from tests.eval.golden_trajectories import GOLDEN_TRAJECTORIES

    if use_mock:
        # Stub-tolerant path: a correctly-behaving mock loop (returns the expected outcome
        # for each trajectory) so the harness + gate run with NO DB / NO cloud. Swap this
        # factory for `_real_loop_factory` once WP-D's AgentSession is complete.
        from tests.eval.mock_loop import build_mock_script

        def loop_factory(traj):
            return MockLoop(build_mock_script(traj))
        report = await run_passk(loop_factory, GOLDEN_TRAJECTORIES, k=k)
    else:
        # Real loop: one AgentSession per repeat, bound to the trajectory actor's Identity.
        # run_passk needs a SYNC factory; resolve identities up-front, then close over them.
        async with async_session_factory() as db:
            from app.agent.loop import AgentSession
            id_cache: dict[str, Identity] = {}
            for t in GOLDEN_TRAJECTORIES:
                if t.actor_email not in id_cache:
                    id_cache[t.actor_email] = await _identity_for(db, t.actor_email)

            def loop_factory(traj):
                return AgentSession(db, id_cache[traj.actor_email])
            report = await run_passk(loop_factory, GOLDEN_TRAJECTORIES, k=k)

    print("pass^k report:", report.as_dict())
    gate = evaluate_gate(report)
    if gate.passed:
        print("RESULT: PASS")
        return 0
    print("RESULT: FAIL (block merge)")
    for r in gate.reasons:
        print("  -", r)
    return 1


if __name__ == "__main__":
    import asyncio

    argv = sys.argv[1:]
    if "--passk" in argv:
        use_mock = "--mock" in argv
        k = 8
        for a in argv:
            if a.startswith("--k="):
                k = int(a.split("=", 1)[1])
        sys.exit(asyncio.run(passk_main(use_mock=use_mock, k=k)))
    sys.exit(asyncio.run(main(argv[0] if argv else None)))
