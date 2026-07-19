"""P0.3 — the final-answer guard (verify-gate + Consultant critic + citation hygiene) must run
on EVERY terminal, not just the sync path. Regression for the SSE-bypasses-critic finding:
previously review_consultant_answer ran only in _finish_answer, so the streaming terminals
(_finalize_streamed_answer, _stream_answer) shipped answers the prerequisite critic never saw.

Pure-unit: no DB, no LLM. We drive _guard_final directly and each streaming terminal with a
fake consultant turn whose prerequisite guard must fire.
"""
from __future__ import annotations

import asyncio

from app.consultant.contracts import GoalFrame, TaskState
from app.consultant.service import PreparedConsultantTurn
from app.consultant.contracts import ContextManifest


def _financial_turn_before_report() -> PreparedConsultantTurn:
    """A close-workflow turn parked at a pre-report node — answering 'mở báo cáo' must warn."""
    return PreparedConsultantTurn(
        frame=GoalFrame(goal_type="financial_statements_ready"),
        state=TaskState(current_node="posting_checked"),
        workflow=None,
        manifest=ContextManifest(goal_type="financial_statements_ready"),
        prompt_block="",
    )


def _session():
    from app.agent.loop import AgentSession

    s = object.__new__(AgentSession)     # no DB/identity needed for the pure guard
    s._consultant_turn = _financial_turn_before_report()
    s._turn_contract = None
    return s


_ANSWER = "Bạn vào báo cáo tài chính ở menu để xem ngay."   # contains 'vao bao cao' trigger


def test_guard_applies_critic_prefix_sync():
    s = _session()
    safe, grounded, unmatched, cites, notice = s._guard_final(_ANSWER, [], [])
    assert "khóa sổ" in safe, "critic prerequisite warning must be present in the guarded answer"
    assert notice and "khóa sổ" in notice, "notice must expose the critic prefix for streamers"


def test_guard_masks_ungrounded_money_on_knowledge_turn():
    """D0.2: a money figure not in the question/context is masked on the real chat guard path."""
    from app.agent.loop import AgentSession
    from app.rag.number_integrity import MASK

    s = object.__new__(AgentSession)
    s._consultant_turn = None
    s._turn_contract = None
    s._turn_question = "số tiền 54,500,000 chịu thuế 10%"
    s._turn_context_text = "Hướng dẫn nhập phiếu chi."
    # model invents a pre-tax figure 49,050,000 not present in question/context
    safe, grounded, unmatched, cites, notice = s._guard_final(
        "Trước thuế 49,050,000; tổng 54,500,000.", [], [])
    assert 49_050_000 in unmatched
    assert MASK in safe and "49,050,000" not in safe
    assert "54,500,000" in safe          # the figure the user supplied survives


def test_finalize_streamed_answer_surfaces_critic_notice():
    """The default knowledge terminal streams the body live, then must emit the critic notice."""
    s = _session()

    class _Streamer:
        full = _ANSWER

        def finalize(self):
            return ""

    async def drive():
        events = []
        # patch the two best-effort persistence/close hooks to no-ops (no DB)
        async def _noop(*a, **k):
            return None
        s._safe_recall_add = _noop
        s._close_run = _noop
        s._msg_ids = lambda *_a, **_k: {}
        s.run_mode = "auto"
        s.session_id = __import__("uuid").uuid4()
        s._routed_cloud = False
        async for ev in s._finalize_streamed_answer(_Streamer(), []):
            events.append(ev)
        return events

    events = asyncio.run(drive())
    notice_deltas = [e for e in events if e.get("type") == "answer" and "khóa sổ" in e.get("delta", "")]
    assert notice_deltas, "SSE knowledge terminal must surface the critic warning as a delta"
