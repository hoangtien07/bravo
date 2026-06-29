"""Constrained-agentic ReAct loop (ADR-0010, WP-D) — single-agent, control-flow-in-code.

The loop is SHORT and its control flow lives HERE, in Python — the LLM never owns it
(ADR-0010, invariant #2/#3). Each step:

  retrieve (RLS-in-SQL) -> llm_structured(tools) -> call_tool (RLS #2 + HITL) -> observe
    -> repeat (<= Budget) -> answer -> verify_numbers (WP-B) -> safe_answer + citations

Pydantic AI is used ONLY as a structured-output library (CONTRACTS §6): it validates the
LLM's `{action,tool,args}` decision into a typed object. The actual model call still goes
through `router.chat` (WP-C) so the egress audit / fail-closed-to-local path is preserved
(invariant #4). We feed router.chat's text into a Pydantic AI FunctionModel purely to parse
it — Pydantic AI never owns the model connection nor the loop.

Cross-WP seams (CONTRACTS §3.1) wired here — ALL REAL now (integration done):
  - verify_numbers (WP-B) — REAL.
  - router.chat   (WP-C) — REAL: pass `context=chunks+engine_values` + `db`; router auto-
    classifies sensitivity (fail-closed local) and audits-then-egresses. `routed_cloud` is
    threaded into the step result for the pass^k egress HARD-FAIL detector (WP-H).
  - create_draft  (WP-E) — via tools.call_tool; today's draft_queue signature is honoured.
  - metric tools  (WP-F) — REAL: `_metric_lookup` -> semantic.execute(MockDataSource) (RLS
    at the number tier); `identity` is injected by call_tool.
  - frame_untrusted (WP-G) — RAG chunks framed as inert data before the prompt.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.memory import MemoryStore
from app.agent.tools import REGISTRY, call_tool, filter_tools_by_permission, register
from app.config import get_settings
from app.data_layer.grounding import verify_numbers
from app.data_layer.semantic import MetricResult
from app.llm import router as llm
from app.rag import retriever
from app.security.rls import Identity, frame_untrusted

_settings = get_settings()

# Pydantic AI as a pure structured-output validator (no model ownership).
from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelResponse, TextPart


# --------------------------------------------------------------------------------------
# Budget — circuit breaker (CONTRACTS §2.7). ENFORCED hard before every LLM/tool call.
# --------------------------------------------------------------------------------------
@dataclass
class Budget:
    max_steps: int = 4          # đặt theo reliability_horizon (spike); demo tạm 4
    max_tokens: int = 8000
    deadline_s: float = 30.0


class BudgetExceeded(Exception):
    """Raised internally when a budget dimension is exhausted -> loop stops + audits."""

    def __init__(self, dimension: str, detail: str):
        self.dimension = dimension
        self.detail = detail
        super().__init__(f"Budget vượt ngưỡng: {dimension} ({detail})")


class _BudgetTracker:
    def __init__(self, budget: Budget):
        self.budget = budget
        self.steps = 0
        self.tokens = 0
        self.started = time.monotonic()

    def check(self) -> None:
        """Hard gate — called BEFORE each LLM/tool call. Raises if any dimension is spent."""
        if self.steps >= self.budget.max_steps:
            raise BudgetExceeded("max_steps", f"{self.steps}/{self.budget.max_steps}")
        if self.tokens >= self.budget.max_tokens:
            raise BudgetExceeded("max_tokens", f"{self.tokens}/{self.budget.max_tokens}")
        elapsed = time.monotonic() - self.started
        if elapsed >= self.budget.deadline_s:
            raise BudgetExceeded("deadline_s", f"{elapsed:.1f}/{self.budget.deadline_s}s")


# --------------------------------------------------------------------------------------
# Structured decision schema — Pydantic AI validates the LLM output INTO this.
# --------------------------------------------------------------------------------------
class AgentDecision(BaseModel):
    """The ONLY shape the LLM may emit each step. Control flow keys off `action`."""
    action: Literal["tool", "answer", "clarify"]
    tool: str | None = None                       # required when action == "tool"
    args: dict = Field(default_factory=dict)
    answer: str | None = None                     # final natural-language answer
    question: str | None = None                   # clarifying question (action == "clarify")


async def _parse_decision(text: str) -> AgentDecision:
    """Validate raw LLM text into AgentDecision.

    Robust hơn: model mạnh (gpt-4o) đôi khi bọc JSON trong ```json hoặc kèm prose -> trước
    tiên dọn rào code + trích object JSON đầu tiên rồi json.loads. Thất bại mới fallback sang
    Pydantic AI FunctionModel (CONTRACTS §6). Invalid hẳn -> raise -> caller clarify.
    """
    import re as _re

    raw = (text or "").strip()
    cleaned = raw
    if cleaned.startswith("```"):
        cleaned = _re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = _re.sub(r"\n?```$", "", cleaned).strip()
    m = _re.search(r"\{.*\}", cleaned, _re.DOTALL)
    if m:
        try:
            return AgentDecision(**json.loads(m.group(0)))
        except Exception:
            pass
    # Model mạnh đôi khi trả PROSE không bọc JSON -> coi cả text là câu trả lời (graceful),
    # tránh "clarify" cụt khó hiểu. (Bỏ fallback FunctionModel — nguồn lỗi 'Exceeded retries'.)
    return AgentDecision(
        action="answer",
        answer=raw or "Không tìm thấy thông tin trong tài liệu nội bộ.")


_SYSTEM = (
    "Bạn là BRAVO AI Copilot — trợ lý ERP/kế toán, trả lời TIẾNG VIỆT.\n"
    "Ở MỖI bước bạn PHẢI xuất DUY NHẤT một object JSON (không kèm văn bản, KHÔNG dùng ```), "
    "đúng MỘT trong ba dạng:\n"
    '  {"action":"tool","tool":"<tên>","args":{...}}\n'
    '  {"action":"clarify","question":"<câu hỏi làm rõ>"}\n'
    '  {"action":"answer","answer":"<câu trả lời tiếng Việt>"}\n'
    "ƯU TIÊN action=answer. Nếu NGỮ CẢNH có thông tin liên quan câu hỏi -> PHẢI trả lời "
    "(câu hỏi rộng -> trả lời TỔNG QUAN có cấu trúc rồi mời hỏi sâu); KHÔNG hỏi lại chỉ để "
    "thu hẹp phạm vi.\n"
    "QUY TẮC khi action=answer:\n"
    "- CHỈ dùng NGỮ CẢNH (các khối [1],[2],...) và LỊCH SỬ; KHÔNG dùng kiến thức ngoài, KHÔNG bịa.\n"
    "- Gắn trích dẫn [N] vào mỗi ý lấy từ ngữ cảnh (đúng số khối nguồn).\n"
    "- Nếu NGỮ CẢNH KHÔNG liên quan / không chứa câu trả lời -> answer = 'Không tìm thấy thông "
    "tin trong tài liệu nội bộ.'\n"
    "- Phân biệt CHÍNH XÁC: mua hàng ≠ bán hàng; đầu vào ≠ đầu ra; phải thu ≠ phải trả; nhập ≠ xuất.\n"
    "- KHÔNG tự sinh số liệu — số phải đến từ tool/engine.\n"
    "CHỈ dùng action=clarify khi câu hỏi KHÔNG liên quan ngữ cảnh, HOẶC thiếu tham số bắt buộc "
    "để gọi tool — KHÔNG clarify khi đã có ngữ cảnh liên quan.\n"
    "TUYỆT ĐỐI chỉ xuất JSON."
)


# --------------------------------------------------------------------------------------
# Built-in tools. kb_search = REAL (RAG). metric_* = STUB behind a real schema (WP-F swaps fn).
# --------------------------------------------------------------------------------------
def _register_builtin_tools() -> None:
    if "kb_search" not in REGISTRY:
        register(
            "kb_search",
            json_schema={"type": "object",
                         "properties": {"q": {"type": "string", "description": "truy vấn"}},
                         "required": ["q"]},
            read_only=True,
        )(_noop_kb_search)  # real retrieval is injected per-session (needs db/identity)

    if "metric_lookup" not in REGISTRY:
        register(
            "metric_lookup",
            json_schema={"type": "object",
                         "properties": {"metric_id": {"type": "string"},
                                        "params": {"type": "object"}},
                         "required": ["metric_id"]},
            read_only=True,
            required_permission="metric:read",   # RLS-gated (CONTRACTS §2.2)
        )(_metric_lookup)

    if "create_journal_entry" not in REGISTRY:
        register(
            "create_journal_entry",
            json_schema={"type": "object",
                         "properties": {"account": {"type": "string"},
                                        "amount": {"type": "number"},
                                        "memo": {"type": "string"}},
                         "required": ["account", "amount"]},
            read_only=False,                      # WRITE -> draft only (invariant #2)
            required_permission="draft:create",
        )(_stub_create_journal_entry)


def _noop_kb_search(**kwargs):  # placeholder fn; the loop performs retrieval directly
    return {"note": "kb_search được loop thực thi trực tiếp với db+identity (RLS-in-SQL)."}


def _metric_lookup(metric_id: str, params: dict | None = None, *, identity: Identity):
    """REAL (WP-F seam): engine số liệu qua semantic.execute -> MockDataSource (RLS tầng số).

    LLM đã chọn metric_id; engine TÍNH deterministic (ADR-0004/0005 — LLM không sinh số).
    Metric ngoài registry / thiếu quyền (chỉ tiêu nhạy) / không có dữ liệu DEMO -> raise ->
    call_tool trả {isError} -> loop quan sát lỗi -> ABSTAIN (không bịa). `identity` được
    call_tool tiêm vào (tools.py) để áp RLS."""
    from app.data_layer.mock_source import MockDataSource
    from app.data_layer.semantic import MetricQuery, execute
    return execute(MetricQuery(metric_id, params or {}), MockDataSource(), identity)


def _stub_create_journal_entry(**kwargs):  # never executed (write -> draft); here for schema
    return {"note": "stub — đường ghi đi qua draft_queue.create_draft (WP-E)."}


_register_builtin_tools()


# --------------------------------------------------------------------------------------
# The agent session / loop.
# --------------------------------------------------------------------------------------
class AgentSession:
    def __init__(self, db: AsyncSession, identity: Identity,
                 session_id: uuid.UUID | None = None, budget: Budget | None = None):
        self.db = db
        self.identity = identity
        self.session_id = session_id or uuid.uuid4()
        self.memory = MemoryStore(db, self.session_id, identity)
        self.budget = budget or Budget()
        self.agent_run_id = uuid.uuid4()

    async def _llm_decide(self, messages: list[dict],
                          context_objs: list) -> tuple[AgentDecision, int]:
        """One structured step: router.chat (auto-classify egress, audited) -> Pydantic AI validate.

        Router TỰ phân loại độ nhạy từ `context_objs` (chunks + metric-results) — fail-closed →
        local (WP-C seam-1, invariant #4). Demo cho phép cloud với ngữ cảnh KHÔNG nhạy; số liệu
        tài chính THẬT (is_demo=False) → local. `db` để audit-then-egress trước khi rời mạng.
        """
        text, _decision = await llm.chat(
            messages, context=context_objs, db=self.db,
            allow_cloud_task=_settings.demo_allow_cloud_answers, temperature=0.1)
        # Track egress: if ANY llm call this turn routed to cloud, the turn is cloud-routed
        # (the pass^k egress HARD-FAIL detector keys off `routed_cloud` in the step result).
        if getattr(_decision, "backend", "local") == "cloud":
            self._routed_cloud = True
        approx_tokens = len(text) // 4 + sum(len(m["content"]) for m in messages) // 4
        return await _parse_decision(text), approx_tokens

    async def _audit(self, action: str, detail: dict) -> None:
        """Best-effort audit. Budget-stop and tool events are auditable (ADR-0010)."""
        try:
            from app.database.models import AuditLog
            self.db.add(AuditLog(actor_id=self.identity.employee_id, action=action, detail=detail))
            await self.db.commit()
        except Exception:
            # Audit must never crash the turn; in pure-unit tests db may be a stub.
            pass

    # --- durable AgentRun (W2.2/2.3) — best-effort, không làm vỡ lượt nếu DB lỗi/giả ---
    async def _open_run(self) -> None:
        try:
            from app.agent import runs
            await runs.start_run(self.db, run_id=self.agent_run_id, session_id=self.session_id,
                                 employee_id=self.identity.employee_id)
        except Exception:
            pass

    async def _close_run(self, status: str) -> None:
        try:
            from app.agent import runs
            await runs.finish_run(self.db, self.agent_run_id, status=status, checkpoint_state={
                "created_draft": getattr(self, "_created_draft", False),
                "routed_cloud": getattr(self, "_routed_cloud", False)})
        except Exception:
            pass

    def _terminal_status(self) -> str:
        # Lượt có tạo bút toán/draft chờ duyệt -> paused_for_approval ("duyệt = thực thi").
        return "paused_for_approval" if getattr(self, "_created_draft", False) else "done"

    async def _safe_recall_prompt(self, limit: int = 20) -> list[dict[str, str]]:
        """Lịch sử hội thoại đã DATA-frame (best-effort — DB giả ở unit-test -> [])."""
        try:
            return await self.memory.recall_recent_for_prompt(limit=limit)
        except Exception:
            return []

    async def _summarize(self, history_text: str, prev_summary: str | None) -> str:
        """Tóm tắt phần hội thoại cũ (giữ sự kiện/quyết định/số) — đi qua router (egress-audited)."""
        prompt = [
            {"role": "system", "content": (
                "Tóm tắt cuộc hội thoại sau bằng TIẾNG VIỆT, gạch đầu dòng ngắn gọn: giữ lại "
                "CHỦ ĐỀ đang bàn, SỰ KIỆN, QUYẾT ĐỊNH, và DỮ LIỆU/số quan trọng. Nếu có TÓM TẮT "
                "TRƯỚC thì hợp nhất, không lặp.")},
            {"role": "user", "content": (
                (f"TÓM TẮT TRƯỚC:\n{prev_summary}\n\n" if prev_summary else "")
                + f"HỘI THOẠI:\n{history_text}\n\nTÓM TẮT:")},
        ]
        try:
            text, _ = await llm.chat(prompt, db=self.db,
                                     allow_cloud_task=_settings.demo_allow_cloud_answers,
                                     temperature=0.2)
            return (text or prev_summary or "").strip()
        except Exception:
            return prev_summary or ""

    async def _safe_history(self) -> list[dict[str, str]]:
        """Lịch sử CÓ NÉN (Tầng 2). Lỗi -> fallback recall thô 20 lượt (giữ lượt chạy được)."""
        try:
            return await self.memory.history_for_prompt(self._summarize)
        except Exception:
            return await self._safe_recall_prompt(limit=20)

    async def _rephrase_query(self, recall: list[dict], question: str, max_turns: int = 6) -> str:
        """Câu nối tiếp ngắn -> câu truy vấn ĐỘC LẬP dùng lịch sử (DocsGPT pattern). Lượt đầu
        (không lịch sử) -> giữ nguyên. Lỗi -> fallback câu gốc. Đi qua router (egress-audited)."""
        if not recall:
            return question
        hist = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in recall[-max_turns:])
        prompt = [
            {"role": "system", "content": (
                "Viết lại CÂU HỎI MỚI thành MỘT câu truy vấn tìm kiếm độc lập bằng tiếng Việt, "
                "bổ sung ngữ cảnh cần thiết từ LỊCH SỬ (giữ thuật ngữ nghiệp vụ; phân biệt "
                "mua/bán, đầu vào/đầu ra, phải thu/phải trả). CHỈ trả về câu truy vấn, không giải thích.")},
            {"role": "user",
             "content": f"LỊCH SỬ:\n{hist}\n\nCÂU HỎI MỚI: {question}\n\nCÂU TRUY VẤN ĐỘC LẬP:"},
        ]
        try:
            text, _ = await llm.chat(prompt, db=self.db,
                                     allow_cloud_task=_settings.demo_allow_cloud_answers,
                                     temperature=0.0)
            q = (text or "").strip().strip('"').splitlines()[0].strip() if text else ""
            return q or question
        except Exception:
            return question

    async def _source_labels(self, chunks: list) -> dict[str, str]:
        """Map source_id -> nhãn thân thiện (knowledge_type/filename) thay UUID trong trích dẫn."""
        ids = {getattr(c, "source_id", None) for c in chunks}
        ids.discard(None)
        if not ids:
            return {}
        try:
            from sqlalchemy import select
            from app.database.models import Source
            rows = (await self.db.execute(
                select(Source).where(Source.id.in_([uuid.UUID(x) for x in ids])))).scalars().all()
            return {str(s.id): (s.knowledge_type or s.filename) for s in rows}
        except Exception:
            return {}

    async def _prepare_turn(self, user_message: str):
        """Retrieve (query-rewrite theo lịch sử) + build messages có NGỮ CẢNH đánh số [N].
        Dùng chung step()/step_stream(). Trả (messages, chunks, citations) — citations[i] khớp [i+1]."""
        recall = await self._safe_history()                 # lịch sử (CÓ NÉN) TRƯỚC câu hiện tại
        await self._safe_recall_add("user", user_message)

        search_query = await self._rephrase_query(recall, user_message)
        chunks = await retriever.retrieve(self.db, self.identity, search_query, top_n=6)

        labels = await self._source_labels(chunks)
        blocks: list[str] = []
        citations: list[str] = []
        for i, c in enumerate(chunks, start=1):
            sid = getattr(c, "source_id", None)
            label = labels.get(sid) if sid else None
            if label:  # tên nguồn thân thiện (chương/file) + vị trí
                loc = []
                if getattr(c, "page_number", None) is not None:
                    loc.append(f"trang {c.page_number}")
                if getattr(c, "sheet_name", None):
                    loc.append(f"sheet {c.sheet_name}")
                if getattr(c, "cell_range", None):
                    loc.append(f"ô {c.cell_range}")
                cite = label + (", " + ", ".join(loc) if loc else "")
            else:  # fallback: dùng citation gốc của chunk (UUID) nếu chưa join được tên
                cite = c.citation() if hasattr(c, "citation") else "tài liệu"
            citations.append(cite)   # citations[i-1] <-> khối [i] <-> FE source-i (bấm-cuộn)
            # Nội dung tài liệu là DỮ LIỆU không tin cậy (WP-G) -> frame trơ, không phải chỉ thị.
            blocks.append(f"[{i}] {frame_untrusted(c.content, source=sid)}\n(nguồn [{i}]: {cite})")
        context = "\n\n".join(blocks)

        tools = filter_tools_by_permission(REGISTRY, self.identity)  # RLS layer #1
        tools_desc = "\n".join(
            f"- {t.name}(schema={json.dumps(t.json_schema, ensure_ascii=False)})"
            f"{' [GHI->nháp]' if not t.read_only else ''}" for t in tools)

        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "system", "content": f"TOOL khả dụng:\n{tools_desc or '(không có)'}"},
            *recall,  # multi-turn: lịch sử (đã DATA-frame) NẰM TRƯỚC câu hỏi
            {"role": "user",
             "content": f"NGỮ CẢNH (đánh số để trích dẫn [N]):\n{context or '(trống)'}\n\nCÂU HỎI: {user_message}"},
        ]
        return messages, chunks, citations

    async def step(self, user_message: str) -> dict:
        """One conversational turn. Control flow is fully in this method (ADR-0010)."""
        tracker = _BudgetTracker(self.budget)
        self._routed_cloud = False             # set True by _llm_decide if a call hits cloud
        self._created_draft = False            # set True khi tool ghi tạo draft chờ duyệt
        self.agent_run_id = uuid.uuid4()       # 1 lượt = 1 AgentRun (drafts của lượt link vào)
        await self._open_run()

        messages, chunks, citations = await self._prepare_turn(user_message)

        engine_values: list[MetricResult] = []
        observations: list[str] = []

        # 2) ReAct loop — SHORT, budget-gated BEFORE each LLM/tool call.
        try:
            while True:
                tracker.check()                       # hard gate before the LLM call
                try:
                    decision, used = await self._llm_decide(messages, chunks + engine_values)
                except Exception as e:                # malformed structured output -> clarify
                    return await self._finish_clarify(
                        f"Tôi chưa hiểu rõ yêu cầu, bạn nói rõ hơn được không? ({e})", citations)
                tracker.tokens += used
                tracker.steps += 1                    # an LLM decision counts as a step

                if decision.action == "clarify":
                    return await self._finish_clarify(
                        decision.question or "Bạn có thể nói rõ hơn yêu cầu không?", citations)

                if decision.action == "answer":
                    return await self._finish_answer(decision.answer or "", engine_values, citations)

                # action == "tool"
                if not decision.tool:
                    return await self._finish_clarify(
                        "Yêu cầu chưa rõ tool/tham số cần dùng.", citations)

                tracker.check()                       # hard gate before the tool call too
                result = await call_tool(
                    decision.tool, decision.args, self.identity,
                    db=self.db, agent_run_id=self.agent_run_id)
                await self._audit("agent.tool_call",
                                  {"tool": decision.tool, "isError": result.get("isError", False)})

                # Tool ghi -> draft chờ duyệt: đánh dấu để lượt vào trạng thái paused_for_approval.
                if result.get("is_write") or result.get("status") == "pending_approval":
                    self._created_draft = True

                # Harvest engine values for the verify-gate (numbers come from tools, not LLM).
                ev = result.get("result")
                if isinstance(ev, MetricResult):
                    engine_values.append(ev)
                elif isinstance(ev, list):
                    engine_values.extend(x for x in ev if isinstance(x, MetricResult))

                observations.append(f"[{decision.tool}] -> {self._obs_str(result)}")
                messages.append({"role": "assistant",
                                 "content": json.dumps(decision.model_dump(), ensure_ascii=False)})
                messages.append({"role": "user",
                                 "content": "QUAN SÁT:\n" + "\n".join(observations)})

        except BudgetExceeded as be:
            await self._audit("agent.budget_exceeded",
                              {"dimension": be.dimension, "detail": be.detail,
                               "steps": tracker.steps})
            answer = ("Tôi đã dừng vì đạt giới hạn an toàn của phiên xử lý "
                      f"({be.dimension}). Vui lòng thu hẹp câu hỏi hoặc thử lại.")
            await self._safe_recall_add("assistant", answer)
            await self._close_run("failed")
            return {"answer": answer, "grounded": False, "citations": citations,
                    "stopped": "budget", "budget_dimension": be.dimension,
                    "routed_cloud": getattr(self, "_routed_cloud", False),
                    "session_id": str(self.session_id)}

    # --- streaming (P-chat: SSE) ---------------------------------------------------
    @staticmethod
    def _chunk_text(text: str, size: int = 48):
        for i in range(0, len(text), size):
            yield text[i:i + size]

    def _verdict(self, answer: str, engine_values: list, citations: list):
        """Verify-gate (invariant #3) — giống _finish_answer: financial-only. Trả (safe, grounded, unmatched)."""
        if engine_values:
            verdict = verify_numbers(answer, engine_values)
            safe = verdict.safe_answer if not verdict.grounded else answer
            return safe, verdict.grounded, verdict.unmatched
        return answer, bool(citations), []

    async def _stream_answer(self, answer: str, engine_values: list, citations: list):
        # Verify-gate chạy trên answer ĐẦY ĐỦ TRƯỚC khi stream (không lọt số chưa kiểm chứng).
        safe, grounded, unmatched = self._verdict(answer, engine_values, citations)
        await self._safe_recall_add("assistant", safe)
        await self._close_run(self._terminal_status())
        for ch in self._chunk_text(safe):
            yield {"type": "answer", "delta": ch}
        yield {"type": "done", "grounded": grounded, "unmatched": unmatched, "citations": citations,
               "routed_cloud": getattr(self, "_routed_cloud", False), "session_id": str(self.session_id)}

    async def _stream_clarify(self, question: str, citations: list):
        await self._safe_recall_add("assistant", question)
        await self._close_run(self._terminal_status())
        for ch in self._chunk_text(question):
            yield {"type": "answer", "delta": ch}
        yield {"type": "done", "grounded": True, "clarify": True, "citations": citations,
               "routed_cloud": getattr(self, "_routed_cloud", False), "session_id": str(self.session_id)}

    async def step_stream(self, user_message: str):
        """STREAMING của step() — async generator yield event dict cho SSE. Tái dùng
        _prepare_turn + budget + AgentRun lifecycle. Bước DECIDE không stream (JSON strict);
        chỉ câu trả lời cuối stream (chunk chuỗi)."""
        tracker = _BudgetTracker(self.budget)
        self._routed_cloud = False
        self._created_draft = False
        self.agent_run_id = uuid.uuid4()
        await self._open_run()
        yield {"type": "id", "conversation_id": str(self.session_id),
               "agent_run_id": str(self.agent_run_id)}
        try:
            messages, chunks, citations = await self._prepare_turn(user_message)
            yield {"type": "source", "citations": citations}
            engine_values: list[MetricResult] = []
            observations: list[str] = []
            while True:
                tracker.check()
                try:
                    decision, used = await self._llm_decide(messages, chunks + engine_values)
                except Exception as e:
                    async for ev in self._stream_clarify(
                            f"Tôi chưa hiểu rõ yêu cầu, bạn nói rõ hơn được không? ({e})", citations):
                        yield ev
                    return
                tracker.tokens += used
                tracker.steps += 1
                yield {"type": "step", "action": decision.action, "step_n": tracker.steps}

                if decision.action == "clarify":
                    async for ev in self._stream_clarify(
                            decision.question or "Bạn có thể nói rõ hơn không?", citations):
                        yield ev
                    return
                if decision.action == "answer":
                    async for ev in self._stream_answer(decision.answer or "", engine_values, citations):
                        yield ev
                    return
                if not decision.tool:
                    async for ev in self._stream_clarify("Yêu cầu chưa rõ tool/tham số.", citations):
                        yield ev
                    return

                tracker.check()
                yield {"type": "tool_call", "tool": decision.tool, "args": decision.args}
                result = await call_tool(decision.tool, decision.args, self.identity,
                                         db=self.db, agent_run_id=self.agent_run_id)
                await self._audit("agent.tool_call",
                                  {"tool": decision.tool, "isError": result.get("isError", False)})
                yield {"type": "tool_result", "tool": decision.tool,
                       "isError": result.get("isError", False), "summary": self._obs_str(result)}
                if result.get("is_write") or result.get("status") == "pending_approval":
                    self._created_draft = True
                    yield {"type": "draft", "draft_id": result.get("draft_id"),
                           "kind": decision.tool, "payload": decision.args}

                ev = result.get("result")
                if isinstance(ev, MetricResult):
                    engine_values.append(ev)
                elif isinstance(ev, list):
                    engine_values.extend(x for x in ev if isinstance(x, MetricResult))
                observations.append(f"[{decision.tool}] -> {self._obs_str(result)}")
                messages.append({"role": "assistant",
                                 "content": json.dumps(decision.model_dump(), ensure_ascii=False)})
                messages.append({"role": "user",
                                 "content": "QUAN SÁT:\n" + "\n".join(observations)})
        except BudgetExceeded as be:
            await self._audit("agent.budget_exceeded",
                              {"dimension": be.dimension, "steps": tracker.steps})
            answer = ("Tôi đã dừng vì đạt giới hạn an toàn của phiên xử lý "
                      f"({be.dimension}). Vui lòng thu hẹp câu hỏi hoặc thử lại.")
            await self._safe_recall_add("assistant", answer)
            await self._close_run("failed")
            yield {"type": "answer", "delta": answer}
            yield {"type": "done", "grounded": False, "stopped": "budget", "citations": citations,
                   "routed_cloud": getattr(self, "_routed_cloud", False),
                   "session_id": str(self.session_id)}

    # --- terminal helpers ---------------------------------------------------------
    async def _finish_answer(self, answer: str, engine_values: list[MetricResult],
                             citations: list[str]) -> dict:
        """Verify-gate (WP-B, invariant #3) — applied to FINANCIAL numbers only.

        The number-mask gate is a FINANCIAL-ANALYTICS control: it runs only when the agent
        actually consulted the metric engine this turn (engine_values present) — then EVERY
        number in the answer must trace to an engine value (strict, invariant #3). A pure
        KB/narrative answer (no engine values) is NOT number-gated: its prose numbers (list
        steps, 'Điều 5', years, amounts quoted from the cited document) are not engine claims.
        Such an answer is grounded iff it was produced from retrieved context (has citations).
        """
        if engine_values:
            verdict = verify_numbers(answer, engine_values)
            safe = verdict.safe_answer if not verdict.grounded else answer
            grounded, unmatched = verdict.grounded, verdict.unmatched
        else:
            safe, grounded, unmatched = answer, bool(citations), []
        await self._safe_recall_add("assistant", safe)
        await self._close_run(self._terminal_status())
        return {
            "answer": safe,
            "grounded": grounded,
            "unmatched": unmatched,
            "citations": citations,
            "routed_cloud": getattr(self, "_routed_cloud", False),
            "session_id": str(self.session_id),
        }

    async def _finish_clarify(self, question: str, citations: list[str]) -> dict:
        await self._safe_recall_add("assistant", question)
        await self._close_run(self._terminal_status())
        return {"answer": question, "grounded": True, "clarify": True,
                "citations": citations, "routed_cloud": getattr(self, "_routed_cloud", False),
                "session_id": str(self.session_id)}

    @staticmethod
    def _obs_str(result: dict) -> str:
        if result.get("isError"):
            return f"LỖI: {result.get('error')}"
        ev = result.get("result")
        if isinstance(ev, MetricResult):
            return f"{ev.metric_id}={ev.value} {ev.scale or ''} ({ev.provenance})"
        if result.get("is_write"):
            return result.get("message", "đã tạo nháp")
        return json.dumps(result, ensure_ascii=False, default=str)[:500]

    async def _safe_recall_add(self, role: str, content: str) -> None:
        try:
            await self.memory.recall_add(role, content)
        except Exception:
            pass  # memory persistence must not crash the turn (stub db in unit tests)
