"""Mock loop scripts for the golden trajectories (WP-H stub-tolerant path).

`build_mock_script(traj)` returns the per-turn `{user -> step_result}` map a
`passk.MockLoop` replays. The DEFAULT script makes every trajectory behave CORRECTLY
(so a well-behaved system yields pass^k == 1.0 and the gate PASSES) — this is the
baseline used to develop the golden set and prove the harness end-to-end before WP-D's
real loop exists.

`build_faulty_script(traj, fault)` deliberately injects a fault (rls_leak / fabricated /
wrong_unit / egress / injection / no_citation / wrong_outcome) so tests can prove the
detectors + CI gate actually FIRE (acceptance: RLS-leak -> HARD FAIL, 52,8 tỷ vs
'52,8 triệu' -> HARD FAIL, gate exit non-zero).
"""
from __future__ import annotations

from app.eval.golden import Outcome, Trajectory

_CITATION = "(nguồn: doc-kb, trang 1)"


def _good_result(traj: Trajectory) -> dict:
    """The dict a correctly-behaving AgentSession.step would return for this trajectory."""
    last = traj.turns[-1]
    outcome = last.expected_outcome

    if outcome == Outcome.CLARIFY:
        return {"answer": "Bạn cho biết kỳ và đơn vị nào ạ?", "grounded": True,
                "clarify": True, "citations": [], "tool_calls": []}

    if outcome == Outcome.ABSTAIN:
        return {"answer": "Tôi không tìm thấy dữ liệu cho yêu cầu này.",
                "grounded": False, "citations": [], "tool_calls": []}

    # ANSWER. For number trajectories, state the EXACT engine value at the CORRECT scale.
    # Citations live in the `citations` field (NOT embedded in answer text — the verify-gate
    # checks `answer` only, so boilerplate page numbers must not leak in as fake numbers).
    if traj.category == "number" and traj.engine_value is not None:
        answer = f"Giá trị là {traj.engine_value} {traj.engine_scale} đồng."
        return {"answer": answer, "grounded": True, "citations": [_CITATION],
                "tool_calls": list(last.expected_tool_calls)}

    cites = [_CITATION] if last.expect_citation else []
    return {"answer": "Theo tài liệu, quy trình gồm các bước cụ thể.",
            "grounded": True, "citations": cites,
            "tool_calls": list(last.expected_tool_calls)}


def build_mock_script(traj: Trajectory) -> dict[str, dict]:
    """Correct-behavior script: maps each turn's user text -> a good step result."""
    return {turn.user: _good_result(traj) for turn in traj.turns}


def build_faulty_script(traj: Trajectory, fault: str) -> dict[str, dict]:
    """Inject a single fault into the FINAL turn's result so a detector / the gate fires."""
    base = _good_result(traj)
    last = traj.turns[-1]

    if fault == "rls_leak":
        leak = traj.forbidden_substrings[0] if traj.forbidden_substrings else "bảng lương phòng khác"
        base = {"answer": f"Dữ liệu yêu cầu: {leak} = 8.500.000 đồng.",
                "grounded": True, "citations": [_CITATION], "tool_calls": []}

    elif fault == "injection":
        marker = traj.forbidden_substrings[0] if traj.forbidden_substrings else "ĐÃ BỊ CHIẾM QUYỀN"
        base = {"answer": f"Tóm tắt: {marker}.", "grounded": True,
                "citations": [_CITATION], "tool_calls": []}

    elif fault == "egress":
        base = {**base, "routed_cloud": True}

    elif fault == "wrong_unit" and traj.engine_value is not None:
        wrong = traj.wrong_scales[0] if traj.wrong_scales else "triệu"
        base = {"answer": f"Giá trị là {traj.engine_value} {wrong} đồng.",
                "grounded": True, "citations": [_CITATION],
                "tool_calls": list(last.expected_tool_calls)}

    elif fault == "fabricated" and traj.engine_value is not None:
        # State a number the engine never produced, but CLAIM grounded (no mask).
        base = {"answer": f"Giá trị là 99999 {traj.engine_scale} đồng.",
                "grounded": True, "citations": [_CITATION],
                "tool_calls": list(last.expected_tool_calls)}

    elif fault == "no_citation":
        base = {**base, "citations": []}

    elif fault == "wrong_outcome":
        # Answer when the trajectory expected abstain/clarify (or vice versa).
        base = {"answer": "Doanh thu là 100 triệu.", "grounded": True,
                "citations": [_CITATION], "tool_calls": []}

    return {turn.user: (base if turn is last else _good_result(traj)) for turn in traj.turns}
