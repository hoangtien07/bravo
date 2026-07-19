"""P1.3b — the A/B/C0 comparison runner drives arms side by side and isolates arm failures."""
from __future__ import annotations

import asyncio

from app.eval.ab_c0_compare import compare_arms


class _Arm:
    def __init__(self, answer, grounded=True):
        self._answer = answer
        self._grounded = grounded

    async def step(self, q):
        return {"answer": f"{self._answer}: {q}", "grounded": self._grounded, "citations": ["s1"]}


class _BrokenArm:
    async def step(self, q):
        raise RuntimeError("boom")


def test_compare_runs_all_arms_side_by_side():
    factories = {"A": lambda: _Arm("legacy"), "C0": lambda: _Arm("bare")}
    report = asyncio.run(compare_arms(factories, ["Q1", "Q2"]))
    assert report["n_questions"] == 2
    assert report["arms"] == ["A", "C0"]
    first = report["rows"][0]
    assert first["question"] == "Q1"
    arms = {r["arm"]: r for r in first["results"]}
    assert arms["A"]["answer"].startswith("legacy: Q1")
    assert arms["C0"]["answer"].startswith("bare: Q1")


def test_one_broken_arm_does_not_sink_comparison():
    factories = {"A": lambda: _Arm("ok"), "B": lambda: _BrokenArm()}
    report = asyncio.run(compare_arms(factories, ["Q"]))
    arms = {r["arm"]: r for r in report["rows"][0]["results"]}
    assert arms["A"]["answer"].startswith("ok")
    assert "error" in arms["B"] and "boom" in arms["B"]["error"]
