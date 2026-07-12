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
import re
import time
import uuid
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.memory import MemoryStore
from app.agent.bravo_playbooks import load_playbooks, render_playbook_hint
from app.agent.tools import REGISTRY, call_tool, filter_tools_by_permission, register
from app.config import get_settings
from app.data_layer.grounding import verify_numbers
from app.data_layer.semantic import MetricResult
from app.llm import router as llm
from app.rag import retriever
from app.security.rls import Identity, frame_untrusted

_settings = get_settings()

# Pydantic AI as a pure structured-output validator (no model ownership).


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


# JSON schema của AgentDecision cho structured output (W1.3) — dùng cho guided_json (vLLM)
# và tài liệu hoá dạng bắt buộc. Cloud chỉ cần json_object; schema này ép chặt hơn ở local.
_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["tool", "answer", "clarify"]},
        "tool": {"type": ["string", "null"]},
        "args": {"type": "object"},
        "answer": {"type": ["string", "null"]},
        "question": {"type": ["string", "null"]},
    },
    "required": ["action"],
}


def _parse_decision_strict(text: str) -> tuple[AgentDecision, bool]:
    """Validate raw LLM text into (AgentDecision, ok).

    ok=True  -> trích được object JSON hợp lệ thành AgentDecision.
    ok=False -> KHÔNG parse được: coi cả text là câu trả lời prose (graceful, giữ hành vi cũ)
                và báo hiệu để caller có thể RETRY một lần (W1.3).
    Dọn rào ```code``` + trích object JSON đầu tiên rồi json.loads.
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
            return AgentDecision(**json.loads(m.group(0))), True
        except Exception:
            pass
    return AgentDecision(
        action="answer",
        answer=raw or "Không tìm thấy thông tin trong tài liệu nội bộ."), False


async def _parse_decision(text: str) -> AgentDecision:
    """Backward-compat wrapper (giữ chữ ký cũ) — bỏ cờ ok."""
    parsed, _ok = _parse_decision_strict(text)
    return parsed


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
    "- Khi CÓ căn cứ: trả lời CHI TIẾT, có CẤU TRÚC — chia các BƯỚC đánh số, mỗi bước nêu rõ thao "
    "tác cụ thể (menu/màn hình/phím tắt/trường nhập nếu ngữ cảnh có); gạch đầu dòng cho lựa chọn con.\n"
    "- Gắn trích dẫn [N] vào mỗi ý lấy từ ngữ cảnh (đúng số khối nguồn).\n"
    "- Nếu ngữ cảnh CHỈ có một phần: trả lời phần CÓ, nói rõ phần còn thiếu, rồi GỢI Ý người dùng nêu "
    "tên chức năng/màn hình cụ thể để tra tiếp — KHÔNG dừng cụt.\n"
    "- Nếu NGỮ CẢNH KHÔNG liên quan / không chứa câu trả lời -> answer BẮT ĐẦU bằng đúng câu 'Không "
    "tìm thấy thông tin trong tài liệu nội bộ.' (có thể mời người dùng nêu rõ chức năng cần tra).\n"
    "- Phân biệt CHÍNH XÁC: mua hàng ≠ bán hàng; đầu vào ≠ đầu ra; phải thu ≠ phải trả; nhập ≠ xuất.\n"
    "- Với nghiệp vụ BRAVO: CHỨNG TỪ TRƯỚC, HẠCH TOÁN SAU. Khi hỏi tự động hoá mua hàng/AP, "
    "phải xác định loại chứng từ BRAVO và nguồn kế thừa trước khi nói định khoản.\n"
    "- Không đề xuất SQL/update trực tiếp vào ERP; thay bằng draft/checklist/ngoại lệ chờ người duyệt.\n"
    "- Câu hỏi thao tác ưu tiên user guide/mindmap; câu hỏi schema/bảng/procedure ưu tiên tài liệu kỹ thuật; "
    "câu hỏi phạm vi/testcase ưu tiên KQPT/PTNV.\n"
    "- KHÔNG tự sinh số liệu — số phải đến từ tool/engine.\n"
    "CHỈ dùng action=clarify khi câu hỏi KHÔNG liên quan ngữ cảnh, HOẶC thiếu tham số bắt buộc "
    "để gọi tool — KHÔNG clarify khi đã có ngữ cảnh liên quan.\n"
    "TUYỆT ĐỐI chỉ xuất JSON."
)

# Câu abstain ổn định để PHÁT HIỆN (dù prompt cho phép mời người dùng nêu thêm phía sau).
_ABSTAIN_PREFIX = "không tìm thấy thông tin trong tài liệu nội bộ"


def _is_abstain(text: str) -> bool:
    return _ABSTAIN_PREFIX in (text or "").lower()


def _prune_citations(answer: str, citations: list[str]) -> tuple[list[str], bool]:
    """Citation-hygiene: abstain -> KHÔNG nguồn + not grounded. Answer có [N] -> chỉ nguồn thực
    trích. Answer KHÔNG có [N] nhưng là câu trả lời -> giữ toàn bộ citations (grounded narrative,
    giữ nguyên hành vi cũ). Trả (citations_hiển_thị, grounded_theo_citation)."""
    if _is_abstain(answer):
        return [], False
    nums = {int(n) for n in re.findall(r"\[(\d+)\]", answer or "")}
    used = [citations[i - 1] for i in sorted(nums) if 1 <= i <= len(citations)]
    kept = used or citations
    return kept, bool(kept)


# Persona BỀN của agent — core-memory block luôn PIN vào prompt (khác _SYSTEM: đây là "ai/luồng
# nghiệp vụ", không phải giao thức JSON). Trước đây thiếu mắt xích này nên agent 'mất' system
# context giữa các lượt (letta pin memory blocks vào context; bravo chỉ bê table, quên render).
_PERSONA = (
    "Bạn là BRAVO AI Copilot — trợ lý tri thức & nghiệp vụ cho hệ sinh thái BRAVO ERP "
    "(kế toán, mua hàng/AP, kho, bán hàng). Phục vụ người dùng nội bộ theo phòng ban được "
    "phân quyền. Nguyên tắc bất di: chứng từ TRƯỚC, hạch toán SAU; số liệu phải có nguồn "
    "(không nguồn -> nói không tìm thấy); không ghi thẳng ERP, chỉ tạo nháp chờ người duyệt."
)


def _render_business_flows() -> str:
    """Tóm tắt NGẮN các luồng nghiệp vụ BRAVO từ playbooks THẬT (không bịa) -> seed core-memory,
    để agent luôn biết mình hỗ trợ vòng đời nào (không chỉ hint theo từng câu)."""
    try:
        pbs = load_playbooks()
    except Exception:
        return ""
    if not pbs:
        return ""
    lines = ["Các luồng nghiệp vụ BRAVO bạn hỗ trợ:"]
    lines += [f"- {pb.mode}: {pb.usp} (giai đoạn {pb.lifecycle_stage})" for pb in pbs]
    return "\n".join(lines)


def _default_core_blocks() -> dict[str, str]:
    """Core-memory mặc định seed cho mỗi phiên (idempotent). Nguồn: persona tĩnh + playbooks thật."""
    return {"persona": _PERSONA, "business_flows": _render_business_flows()}


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
            # Schema THẬT: bút toán kép nhiều dòng (mỗi dòng Nợ HOẶC Có). LLM chỉ ĐỀ XUẤT;
            # payload_builder VALIDATE cân Nợ=Có trước khi tạo nháp (ADR-0004/0014).
            json_schema={
                "type": "object",
                "properties": {
                    "lines": {
                        "type": "array",
                        "description": "Các dòng bút toán; mỗi dòng chỉ Nợ HOẶC Có (>0).",
                        "items": {
                            "type": "object",
                            "properties": {
                                "account": {"type": "string", "description": "Số hiệu TK (TT99)"},
                                "debit": {"type": "number"},
                                "credit": {"type": "number"},
                                "memo": {"type": "string"},
                                "source_ref": {"type": "string"},
                            },
                            "required": ["account"],
                        },
                    },
                    "invoice": {"type": "object", "description": "Metadata chứng từ (tuỳ chọn)"},
                },
                "required": ["lines"],
            },
            read_only=False,                      # WRITE -> draft only (invariant #2)
            required_permission="draft:create",
            payload_builder=_build_journal_payload,
        )(_stub_create_journal_entry)

    if "preview_journal_entry" not in REGISTRY:
        register(
            "preview_journal_entry",
            # READ-ONLY: lộ money-engine cho chat — xem bút toán của 1 draft journal_entry
            # (RLS-scoped). Số trả về là MetricResult -> verify-gate (invariant #3).
            json_schema={"type": "object",
                         "properties": {"draft_id": {"type": "string",
                                                      "description": "ID bút toán nháp cần xem"}},
                         "required": ["draft_id"]},
            read_only=True,
            required_permission="draft:create",   # AP maker; RLS phòng qua draft_scope_filter
        )(_preview_journal_entry)


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
    return {"note": "đường ghi đi qua draft_queue.create_draft sau payload_builder (WP-E/W1.9)."}


async def _preview_journal_entry(draft_id: str, *, identity: Identity, db: AsyncSession):
    """READ-ONLY: lộ money-engine AP cho chat. Xem BÚT TOÁN của một draft journal_entry (đã dựng
    deterministic từ hoá đơn qua build_journal_entry). Trả list[MetricResult] -> loop harvest vào
    engine_values -> verify-gate: mọi số trong câu trả lời PHẢI khớp số engine (zero-hallucination,
    invariant #3). RLS: chỉ draft trong phạm vi phòng người hỏi (draft_scope_filter). Đây là năng
    lực bravo-insight (chat thuần) KHÔNG có: giải thích bút toán hoá đơn THẬT có số kiểm chứng."""
    import uuid as _uuid
    from decimal import Decimal

    from sqlalchemy import select

    from app.data_layer.semantic import MetricResult
    from app.database.models import Draft
    from app.erp.draft_queue import canonical_draft_kind, draft_scope_filter

    try:
        did = _uuid.UUID(str(draft_id))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError("draft_id không hợp lệ.") from exc
    draft = (await db.execute(select(Draft).where(
        Draft.id == did, draft_scope_filter(identity, action="create")))).scalar_one_or_none()
    if draft is None:  # không tồn tại HOẶC ngoài phạm vi phòng -> ẩn (RLS, không rò tồn tại)
        raise ValueError("Không tìm thấy bút toán nháp trong phạm vi được phép truy cập.")
    if canonical_draft_kind(draft.kind) != "journal_entry":
        raise ValueError(f"Draft {did} không phải bút toán (kind={draft.kind}).")

    payload = draft.payload or {}
    out: list[MetricResult] = []
    for ln in payload.get("lines", []):
        acc = str(ln.get("account", "")).strip()
        tail = "".join([f" · {ln['memo']}" if ln.get("memo") else "",
                        f" · {ln['source_ref']}" if ln.get("source_ref") else ""])
        for side, vi in (("debit", "Nợ"), ("credit", "Có")):
            amt = ln.get(side)
            if amt in (None, "", 0, "0"):
                continue
            out.append(MetricResult(
                metric_id=f"butoan.{acc}.{side}", value=Decimal(str(amt)),
                provenance=f"draft {did} · TK {acc} {vi}{tail}", scale=None))
    for tot, vi in (("total_debit", "Tổng Nợ"), ("total_credit", "Tổng Có")):
        if payload.get(tot) not in (None, ""):
            out.append(MetricResult(metric_id=f"butoan.{tot}", value=Decimal(str(payload[tot])),
                                    provenance=f"draft {did} · {vi}", scale=None))
    return out


def _build_journal_payload(args: dict) -> dict:
    """W1.9: dựng JournalEntryPayload từ đề xuất của LLM và VALIDATE cân Nợ=Có (ADR-0014).

    LLM chỉ đề xuất các dòng; số KHÔNG do LLM tính hợp lệ hoá — model_validator của
    JournalEntryPayload chặn lệch/bịa số. Lỗi -> raise -> call_tool trả isError (không tạo
    nháp hỏng). Kết quả .model_dump(mode='json') KHỚP schema mà journal_export tiêu thụ.
    """
    from app.accounting.journal import InvoiceMeta, JournalEntryPayload, JournalLine
    from app.data_layer import money

    raw_lines = args.get("lines") or []
    lines = [JournalLine(
        account=str(ln.get("account", "")).strip(),
        debit=money.D(ln.get("debit", 0) or 0),
        credit=money.D(ln.get("credit", 0) or 0),
        memo=str(ln.get("memo", "") or ""),
        source_ref=ln.get("source_ref"),
    ) for ln in raw_lines]
    total_debit = money.money_sum([ln.debit for ln in lines])
    total_credit = money.money_sum([ln.credit for ln in lines])
    inv = args.get("invoice") or {}
    payload = JournalEntryPayload(
        invoice=InvoiceMeta(**{k: v for k, v in inv.items() if k in InvoiceMeta.model_fields}),
        lines=lines, total_debit=total_debit, total_credit=total_credit,
        doc_type=args.get("doc_type", "manual_agent"),
    )
    return payload.model_dump(mode="json")


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
        """One structured step: router.chat (auto-classify egress, audited) -> validate.

        Router TỰ phân loại độ nhạy từ `context_objs` (chunks + metric-results) — fail-closed →
        local (WP-C seam-1, invariant #4). `db` để audit-then-egress trước khi rời mạng.

        W1.3: bật structured output (json_schema) để model ép JSON. Nếu output KHÔNG parse được
        thành tool-call hợp lệ -> RETRY đúng 1 lần kèm thông báo lỗi (tính vào budget qua token).
        W1.2: token dùng usage THẬT từ response (fallback ước lượng nếu backend không trả usage).
        """
        text, decision = await llm.chat(
            messages, context=context_objs, db=self.db, json_schema=_DECISION_SCHEMA,
            allow_cloud_task=_settings.demo_allow_cloud_answers, temperature=0.1)
        if getattr(decision, "backend", "local") == "cloud":
            self._routed_cloud = True
        tokens = self._usage_tokens(decision, text, messages)

        parsed, ok = _parse_decision_strict(text)
        if not ok and getattr(self, "_allow_decide_retry", True):
            # Một lần sửa lỗi: nói rõ output sai để model trả đúng JSON. Chống vòng lặp retry
            # vô hạn bằng cờ (chỉ retry 1 lần/lượt-quyết-định).
            retry_msgs = messages + [
                {"role": "assistant", "content": text},
                {"role": "user", "content": (
                    "Output vừa rồi KHÔNG phải một object JSON hợp lệ. Trả lời LẠI, CHỈ một "
                    "object JSON đúng một trong ba dạng đã nêu, KHÔNG kèm văn bản/markdown.")},
            ]
            text2, d2 = await llm.chat(
                retry_msgs, context=context_objs, db=self.db, json_schema=_DECISION_SCHEMA,
                allow_cloud_task=_settings.demo_allow_cloud_answers, temperature=0.0)
            if getattr(d2, "backend", "local") == "cloud":
                self._routed_cloud = True
            tokens += self._usage_tokens(d2, text2, retry_msgs)
            parsed2, ok2 = _parse_decision_strict(text2)
            self._decide_retries = getattr(self, "_decide_retries", 0) + 1
            if ok2:
                return parsed2, tokens
            # Vẫn hỏng -> coi text2 là câu trả lời prose (graceful), giữ hành vi cũ.
            return parsed2, tokens
        return parsed, tokens

    @staticmethod
    def _usage_tokens(decision, text: str, messages: list[dict]) -> int:
        """Token THẬT từ router usage; fallback ước lượng len//4 nếu backend không trả usage."""
        real = int(getattr(decision, "total_tokens", 0) or 0)
        if real > 0:
            return real
        return len(text) // 4 + sum(len(m["content"]) for m in messages) // 4

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
            await runs.finish_run(
                self.db, self.agent_run_id, status=status,
                tokens_used=getattr(self, "_tokens_used", 0),
                checkpoint_state={
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
        # Core-memory (letta pattern): seed persona/luồng-nghiệp-vụ nếu phiên chưa có (idempotent),
        # rồi PIN vào prompt mỗi lượt. Đây là fix cho bug 'thiếu context'.
        try:
            await self.memory.seed_core_defaults(_default_core_blocks())
            core_text = await self.memory.render_core_blocks()
        except Exception:
            core_text = ""   # core-memory là bổ trợ, không được làm hỏng lượt chat

        recall = await self._safe_history()                 # lịch sử (CÓ NÉN) TRƯỚC câu hiện tại
        await self._safe_recall_add("user", user_message)

        search_query = await self._rephrase_query(recall, user_message)
        chunks = await retriever.retrieve(self.db, self.identity, search_query, top_n=12)

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
        playbook_hint = render_playbook_hint(user_message)

        messages = [
            {"role": "system", "content": _SYSTEM},
            *([{"role": "system", "content": core_text}] if core_text else []),
            {"role": "system", "content": f"TOOL khả dụng:\n{tools_desc or '(không có)'}"},
            *([{"role": "system", "content": playbook_hint}] if playbook_hint else []),
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
        self._tokens_used = 0                  # token THẬT tích luỹ cả lượt (W1.2) -> AgentRun
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
                self._tokens_used += used
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
    # W1.4: hết "streaming giả" (cắt chuỗi 48 ký tự). Hai chế độ, tôn trọng verify-gate:
    #   (a) lượt CÓ engine_values (tài chính) -> BUFFER + verify-gate TRƯỚC, phát answer đã kiểm
    #       chứng nguyên khối (KHÔNG token-stream số chưa qua gate — giữ invariant #3 / ADR-0012).
    #   (b) lượt THUẦN TRI THỨC (không engine_values) -> COMPOSE bằng chat_stream: token THẬT từ
    #       model chảy thẳng ra SSE (grounded iff có citation — không bị number-gate).

    _COMPOSE_SYSTEM = (
        "Bạn là BRAVO AI Copilot. Viết CÂU TRẢ LỜI CUỐI bằng TIẾNG VIỆT, văn xuôi (KHÔNG JSON, "
        "KHÔNG markdown rào code). Khi CÓ căn cứ: trả lời CHI TIẾT, có CẤU TRÚC — chia BƯỚC đánh "
        "số, nêu rõ menu/màn hình/trường nhập nếu ngữ cảnh có. CHỈ dùng NGỮ CẢNH đã cho + LỊCH SỬ; "
        "gắn trích dẫn [N] vào mỗi ý lấy từ ngữ cảnh; KHÔNG bịa; KHÔNG tự sinh số. Với nghiệp vụ "
        "BRAVO phải giữ nguyên tắc chứng từ trước, hạch toán sau; không đề xuất SQL/update trực tiếp "
        "vào ERP; ngữ cảnh CHỈ có một phần -> trả lời phần CÓ rồi GỢI Ý người dùng nêu tên chức "
        "năng/màn hình để tra tiếp. Ngữ cảnh không chứa câu trả lời -> BẮT ĐẦU bằng đúng câu "
        "'Không tìm thấy thông tin trong tài liệu nội bộ.'")

    async def _stream_answer(self, answer: str, messages: list, engine_values: list, citations: list):
        if engine_values:
            # (a) tài chính: buffered verify-gate, phát nguyên khối đã kiểm chứng.
            verdict = verify_numbers(answer, engine_values)
            safe = answer if verdict.grounded else verdict.safe_answer
            grounded, unmatched = verdict.grounded, verdict.unmatched
            cites = _prune_citations(safe, citations)[0]  # hygiene: chỉ nguồn thực trích
            await self._safe_recall_add("assistant", safe)
            await self._close_run(self._terminal_status())
            yield {"type": "answer", "delta": safe}
            yield {"type": "done", "grounded": grounded, "unmatched": unmatched,
                   "citations": cites, "routed_cloud": getattr(self, "_routed_cloud", False),
                   "session_id": str(self.session_id)}
            return

        # (b) tri thức: token-stream THẬT (compose) nếu bật cờ; nếu không, phát answer đã quyết
        # nguyên khối (đúng, không cắt giả). engine_values rỗng -> không bị number-gate.
        final = ""
        if _settings.stream_compose_answer:
            compose = [{"role": "system", "content": self._COMPOSE_SYSTEM}, *messages[2:]]
            parts: list[str] = []
            try:
                async for ev in llm.chat_stream(
                        compose, context=engine_values, db=self.db,
                        allow_cloud_task=_settings.demo_allow_cloud_answers, temperature=0.2):
                    if ev["type"] == "delta":
                        parts.append(ev["text"])
                        yield {"type": "answer", "delta": ev["text"]}
                    elif ev["type"] == "done" and getattr(
                            ev.get("decision"), "backend", "local") == "cloud":
                        self._routed_cloud = True
                final = "".join(parts).strip()
            except Exception:
                final = ""
        if not final:  # cờ tắt HOẶC stream hỏng -> phát answer đã quyết (không mất lượt)
            final = answer
            yield {"type": "answer", "delta": final}
        cites, grounded = _prune_citations(final, citations)  # abstain -> 0 nguồn, not grounded
        await self._safe_recall_add("assistant", final)
        await self._close_run(self._terminal_status())
        yield {"type": "done", "grounded": grounded, "unmatched": [],
               "citations": cites, "routed_cloud": getattr(self, "_routed_cloud", False),
               "session_id": str(self.session_id)}

    async def _stream_clarify(self, question: str, citations: list):
        await self._safe_recall_add("assistant", question)
        await self._close_run(self._terminal_status())
        yield {"type": "answer", "delta": question}
        yield {"type": "done", "grounded": True, "clarify": True, "citations": citations,
               "routed_cloud": getattr(self, "_routed_cloud", False), "session_id": str(self.session_id)}

    async def step_stream(self, user_message: str):
        """STREAMING của step() — async generator yield event dict cho SSE. Tái dùng
        _prepare_turn + budget + AgentRun lifecycle. Bước DECIDE không stream (JSON strict);
        câu trả lời cuối: token THẬT từ model (lượt tri thức) hoặc nguyên khối đã verify-gate
        (lượt tài chính) — xem _stream_answer (W1.4)."""
        tracker = _BudgetTracker(self.budget)
        self._routed_cloud = False
        self._created_draft = False
        self._tokens_used = 0
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
                self._tokens_used += used
                tracker.steps += 1
                yield {"type": "step", "action": decision.action, "step_n": tracker.steps}

                if decision.action == "clarify":
                    async for ev in self._stream_clarify(
                            decision.question or "Bạn có thể nói rõ hơn không?", citations):
                        yield ev
                    return
                if decision.action == "answer":
                    async for ev in self._stream_answer(
                            decision.answer or "", messages, engine_values, citations):
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
            citations = _prune_citations(safe, citations)[0]  # hygiene: chỉ nguồn thực trích
        else:
            safe, unmatched = answer, []
            citations, grounded = _prune_citations(safe, citations)  # abstain -> 0 nguồn, not grounded
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
        if isinstance(ev, list) and ev and all(isinstance(x, MetricResult) for x in ev):
            # nhiều số engine (vd bút toán nhiều dòng) -> render từng dòng đọc được cho LLM
            return "\n".join(f"{x.metric_id}={x.value} {x.scale or ''} ({x.provenance})"
                             for x in ev)[:1500]
        if result.get("is_write"):
            return result.get("message", "đã tạo nháp")
        return json.dumps(result, ensure_ascii=False, default=str)[:500]

    async def _safe_recall_add(self, role: str, content: str) -> None:
        try:
            await self.memory.recall_add(role, content)
        except Exception:
            pass  # memory persistence must not crash the turn (stub db in unit tests)
