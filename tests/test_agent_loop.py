"""WP-D — Agent loop (ADR-0010) tests. LLM is ALWAYS mocked (no cloud call).

Covers the acceptance list in WP-D-agent-loop.md:
  - 2-step KB trajectory runs; max_steps exceeded -> stop + audit;
  - read_only=False tool -> draft, NOT executed (0 direct writes);
  - missing permission -> tool absent from prompt AND call_tool returns isError;
  - answer with numbers -> verify_numbers gate -> unmatched masked;
  - clarify when the structured output is ambiguous.
"""
from __future__ import annotations

import json
import uuid
from decimal import Decimal

import pytest

from app.agent import loop as agent_loop
from app.agent.loop import AgentSession, Budget, _BudgetTracker, BudgetExceeded
from app.agent.tools import (
    REGISTRY,
    Tool,
    call_tool,
    filter_tools_by_permission,
)
from app.data_layer.semantic import MetricResult
from app.security.rls import Identity


# --------------------------------------------------------------------------------------
# Fakes / fixtures — no DB, no cloud.
# --------------------------------------------------------------------------------------
class _FakeDB:
    """Minimal stand-in: AuditLog/Draft .add + .commit + .refresh are no-ops/best-effort."""

    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


class _FakeChunk:
    def __init__(self, content):
        self.content = content

    def citation(self):
        return "(nguồn: doc-1, trang 1)"


def _identity(perms=frozenset(), admin=False):
    return Identity(employee_id=uuid.uuid4(), department_ids=[],
                    permissions=frozenset(perms), is_admin=admin)


def _fixed_metric_1000(mq, source, identity):
    """Deterministic engine for verify-gate tests, independent of the YAML fixture:
    any metric -> 1000 triệu. Patches semantic.execute (loop._metric_lookup re-imports it),
    so the gate is tested against a KNOWN engine value, not the real mock data."""
    return MetricResult(metric_id=mq.metric_id, value=Decimal("1000"), provenance="test",
                        unit="VND", scale="triệu", is_demo=True)


@pytest.fixture
def patch_retrieve(monkeypatch):
    async def fake_retrieve(db, identity, query, top_n=6, **kw):
        return [_FakeChunk("Quy trình nghỉ phép: nộp đơn trước 3 ngày.")]
    monkeypatch.setattr(agent_loop.retriever, "retrieve", fake_retrieve)


def _mock_llm(monkeypatch, scripted: list[str]):
    """Patch router.chat to emit a scripted sequence of structured-JSON strings."""
    calls = {"i": 0}

    async def fake_chat(messages, *, sensitive=None, allow_cloud_task=False, **kw):
        i = calls["i"]
        text = scripted[min(i, len(scripted) - 1)]
        calls["i"] += 1
        from app.llm.router import RoutingDecision
        return text, RoutingDecision("local", "qwen", "test")

    monkeypatch.setattr(agent_loop.llm, "chat", fake_chat)
    return calls


# --------------------------------------------------------------------------------------
# Tool registry: schema fields, RLS filter, call_tool defense-in-depth.
# --------------------------------------------------------------------------------------
def test_tool_dataclass_has_contract_fields():
    t = Tool(name="x", fn=lambda: None, json_schema={"type": "object"},
             read_only=False, required_permission="metric:read")
    assert t.json_schema == {"type": "object"}
    assert t.required_permission == "metric:read"
    # write tool: read_only=False forces requires_approval (post_init consistency)
    assert t.read_only is False and t.requires_approval is True


def test_filter_tools_by_permission_hides_unpermitted():
    reg = {
        "open": Tool("open", lambda: 1),
        "gated": Tool("gated", lambda: 1, required_permission="metric:read"),
    }
    no_perm = filter_tools_by_permission(reg, _identity())
    assert {t.name for t in no_perm} == {"open"}            # gated hidden

    with_perm = filter_tools_by_permission(reg, _identity(perms={"metric:read"}))
    assert {t.name for t in with_perm} == {"open", "gated"}

    admin = filter_tools_by_permission(reg, _identity(admin=True))
    assert {t.name for t in admin} == {"open", "gated"}     # admin sees all


@pytest.mark.asyncio
async def test_call_tool_blocks_missing_permission_returns_iserror():
    REGISTRY["_t_gated"] = Tool("_t_gated", lambda: 42, required_permission="metric:read")
    try:
        res = await call_tool("_t_gated", {}, _identity())  # lacks metric:read
        assert res["isError"] is True
        assert "quyền" in res["error"]
    finally:
        REGISTRY.pop("_t_gated", None)


@pytest.mark.asyncio
async def test_call_tool_unknown_tool_iserror_not_raise():
    res = await call_tool("does_not_exist", {}, _identity(admin=True))
    assert res["isError"] is True


@pytest.mark.asyncio
async def test_call_tool_read_tool_executes():
    REGISTRY["_t_read"] = Tool("_t_read", lambda x: x * 2, read_only=True)
    try:
        res = await call_tool("_t_read", {"x": 21}, _identity(admin=True))
        assert res == {"status": "ok", "result": 42}
    finally:
        REGISTRY.pop("_t_read", None)


@pytest.mark.asyncio
async def test_call_tool_read_tool_exception_is_iserror():
    def boom(**_):
        raise RuntimeError("kaboom")
    REGISTRY["_t_boom"] = Tool("_t_boom", boom, read_only=True)
    try:
        res = await call_tool("_t_boom", {}, _identity(admin=True))
        assert res["isError"] is True and "kaboom" in res["error"]
    finally:
        REGISTRY.pop("_t_boom", None)


@pytest.mark.asyncio
async def test_call_tool_write_creates_draft_does_not_execute(monkeypatch):
    """read_only=False -> draft created, fn NEVER called (0 direct writes)."""
    executed = {"n": 0}

    def write_fn(**kwargs):
        executed["n"] += 1
        return "EXECUTED"

    REGISTRY["_t_write"] = Tool("_t_write", write_fn, read_only=False,
                                required_permission="draft:create")

    created = {"n": 0}

    class _Draft:
        id = uuid.uuid4()

    async def fake_create_draft(db, identity, kind, payload, **kw):
        created["n"] += 1
        return _Draft()

    from app.erp import draft_queue
    monkeypatch.setattr(draft_queue, "create_draft", fake_create_draft)

    # Draft do agent tạo phải scope theo phòng (fail-closed) -> identity có đúng 1 phòng ban.
    writer = Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                      permissions=frozenset({"draft:create"}))
    try:
        res = await call_tool("_t_write", {"account": "131", "amount": 100},
                              writer, db=_FakeDB())
        assert res["status"] == "pending_approval"
        assert res["is_write"] is True
        assert created["n"] == 1           # draft created
        assert executed["n"] == 0          # write fn NEVER executed (invariant #2)
    finally:
        REGISTRY.pop("_t_write", None)


# --------------------------------------------------------------------------------------
# Budget circuit breaker.
# --------------------------------------------------------------------------------------
def test_budget_tracker_stops_on_max_steps():
    t = _BudgetTracker(Budget(max_steps=2))
    t.check()
    t.steps = 1
    t.check()
    t.steps = 2
    with pytest.raises(BudgetExceeded) as ei:
        t.check()
    assert ei.value.dimension == "max_steps"


def test_budget_tracker_stops_on_tokens():
    t = _BudgetTracker(Budget(max_tokens=10))
    t.tokens = 11
    with pytest.raises(BudgetExceeded) as ei:
        t.check()
    assert ei.value.dimension == "max_tokens"


# --------------------------------------------------------------------------------------
# Full loop trajectories (LLM mocked).
# --------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_two_step_kb_trajectory(monkeypatch, patch_retrieve):
    """Step 1: LLM calls kb_search. Step 2: LLM answers from observation."""
    _mock_llm(monkeypatch, [
        json.dumps({"action": "tool", "tool": "kb_search", "args": {"q": "nghỉ phép"}}),
        json.dumps({"action": "answer", "answer": "Bạn cần nộp đơn nghỉ phép trước khi nghỉ."}),
    ])
    sess = AgentSession(_FakeDB(), _identity(admin=True), budget=Budget(max_steps=4))
    out = await sess.step("Quy trình nghỉ phép?")
    assert out["grounded"] is True          # no numbers in answer -> verify-gate passes
    assert "nộp đơn" in out["answer"]
    assert out["citations"]


@pytest.mark.asyncio
async def test_kb_answer_with_prose_numbers_not_masked(monkeypatch, patch_retrieve):
    """KB/narrative answer (NO engine values) keeps its prose numbers — the number-mask gate
    is financial-only: it runs only when a metric tool actually produced values. List steps
    ('1.', '2.') must NOT be masked, and the answer is grounded via retrieved context."""
    _mock_llm(monkeypatch, [
        json.dumps({"action": "answer",
                    "answer": "Quy trình gồm 3 bước: 1. Lập đề nghị; 2. Duyệt; 3. Định khoản."}),
    ])
    sess = AgentSession(_FakeDB(), _identity(admin=True))
    out = await sess.step("Quy trình định khoản gồm mấy bước?")
    assert "[số chưa kiểm chứng]" not in out["answer"]
    assert "1." in out["answer"] and "3." in out["answer"]
    assert out["grounded"] is True          # grounded via context (citations), not number-gate


@pytest.mark.asyncio
async def test_max_steps_exceeded_stops_and_audits(monkeypatch, patch_retrieve):
    """LLM keeps calling a tool forever -> budget stops the loop + writes an audit row."""
    _mock_llm(monkeypatch, [
        json.dumps({"action": "tool", "tool": "kb_search", "args": {"q": "x"}}),
    ])
    db = _FakeDB()
    sess = AgentSession(db, _identity(admin=True), budget=Budget(max_steps=2))
    out = await sess.step("vòng lặp vô hạn")
    assert out["grounded"] is False
    assert out["stopped"] == "budget"
    assert out["budget_dimension"] == "max_steps"
    # audit row recorded
    actions = [getattr(o, "action", None) for o in db.added]
    assert "agent.budget_exceeded" in actions


@pytest.mark.asyncio
async def test_clarify_when_ambiguous(monkeypatch, patch_retrieve):
    _mock_llm(monkeypatch, [
        json.dumps({"action": "clarify", "question": "Bạn hỏi kỳ nào?"}),
    ])
    sess = AgentSession(_FakeDB(), _identity(admin=True))
    out = await sess.step("doanh thu?")
    assert out.get("clarify") is True
    assert "kỳ nào" in out["answer"]


@pytest.mark.asyncio
async def test_malformed_structured_output_treated_as_answer(monkeypatch, patch_retrieve):
    # Model mạnh đôi khi trả PROSE không-JSON -> coi là câu trả lời (graceful), không crash/clarify cụt.
    _mock_llm(monkeypatch, ["Đây là câu trả lời dạng văn xuôi."])
    sess = AgentSession(_FakeDB(), _identity(admin=True))
    out = await sess.step("câu hỏi")
    assert out.get("clarify") is not True
    assert "văn xuôi" in out["answer"]


@pytest.mark.asyncio
async def test_verify_gate_masks_unmatched_numbers(monkeypatch, patch_retrieve):
    """Metric tool returns engine value 1000 triệu; LLM answer states a WRONG number -> masked."""
    _mock_llm(monkeypatch, [
        json.dumps({"action": "tool", "tool": "metric_lookup",
                    "args": {"metric_id": "doanh_thu", "params": {}}}),
        # LLM tries to state 9999 triệu which the engine never produced -> must be masked.
        json.dumps({"action": "answer", "answer": "Doanh thu là 9999 triệu đồng."}),
    ])
    monkeypatch.setattr("app.data_layer.semantic.execute", _fixed_metric_1000)
    sess = AgentSession(_FakeDB(), _identity(perms={"metric:read"}))
    out = await sess.step("doanh thu kỳ này?")
    assert out["grounded"] is False
    assert "9999" not in out["answer"]              # unmatched number masked
    assert "[số chưa kiểm chứng]" in out["answer"]


@pytest.mark.asyncio
async def test_verify_gate_passes_matching_number(monkeypatch, patch_retrieve):
    """LLM states the exact engine value (1000 triệu) -> grounded, unmasked."""
    _mock_llm(monkeypatch, [
        json.dumps({"action": "tool", "tool": "metric_lookup",
                    "args": {"metric_id": "doanh_thu", "params": {}}}),
        json.dumps({"action": "answer", "answer": "Doanh thu là 1000 triệu đồng."}),
    ])
    monkeypatch.setattr("app.data_layer.semantic.execute", _fixed_metric_1000)
    sess = AgentSession(_FakeDB(), _identity(perms={"metric:read"}))
    out = await sess.step("doanh thu kỳ này?")
    assert out["grounded"] is True
    assert "1000" in out["answer"]


@pytest.mark.asyncio
async def test_metric_tool_hidden_without_permission(monkeypatch, patch_retrieve):
    """User without metric:read: metric_lookup is NOT in the prompt AND call_tool blocks it."""
    seen_prompts = {"text": ""}

    async def capture_chat(messages, *, sensitive=None, allow_cloud_task=False, **kw):
        seen_prompts["text"] = json.dumps([m["content"] for m in messages], ensure_ascii=False)
        from app.llm.router import RoutingDecision
        return json.dumps({"action": "answer", "answer": "Không tìm thấy."}), \
            RoutingDecision("local", "qwen", "t")

    monkeypatch.setattr(agent_loop.llm, "chat", capture_chat)
    sess = AgentSession(_FakeDB(), _identity())   # no metric:read
    await sess.step("doanh thu?")
    assert "metric_lookup" not in seen_prompts["text"]   # tool not offered to LLM

    # defense-in-depth: even a forged call is blocked.
    res = await call_tool("metric_lookup", {"metric_id": "x"}, _identity())
    assert res["isError"] is True


# --------------------------------------------------------------------------------------
# B (port loop.py): citation-hygiene — abstain KHÔNG đính nguồn; answer [N] -> chỉ nguồn dùng.
# --------------------------------------------------------------------------------------
def test_prune_citations_and_is_abstain():
    from app.agent.loop import _is_abstain, _prune_citations

    cites = ["nguồn A", "nguồn B", "nguồn C"]
    # abstain -> không nguồn, not grounded (dù prompt cho phép mời người dùng nêu thêm phía sau)
    assert _is_abstain("Không tìm thấy thông tin trong tài liệu nội bộ. Hãy nêu tên chức năng.")
    assert _prune_citations("Không tìm thấy thông tin trong tài liệu nội bộ.", cites) == ([], False)
    # answer CÓ [N] -> chỉ nguồn thực trích
    kept, grounded = _prune_citations("Theo [1] và [3] thì ...", cites)
    assert kept == ["nguồn A", "nguồn C"] and grounded is True
    # answer KHÔNG có [N] nhưng là câu trả lời -> giữ toàn bộ (grounded narrative, hành vi cũ)
    kept, grounded = _prune_citations("Bạn cần nộp đơn nghỉ phép trước.", cites)
    assert kept == cites and grounded is True


@pytest.mark.asyncio
async def test_abstain_answer_drops_citations(monkeypatch, patch_retrieve):
    """Abstain -> grounded=False và KHÔNG đính nguồn (dù retrieve có trả chunk)."""
    _mock_llm(monkeypatch, [
        json.dumps({"action": "answer",
                    "answer": "Không tìm thấy thông tin trong tài liệu nội bộ."}),
    ])
    sess = AgentSession(_FakeDB(), _identity(admin=True))
    out = await sess.step("câu hỏi ngoài phạm vi tài liệu")
    assert out["grounded"] is False
    assert out["citations"] == []


def test_clip_abstain_cuts_fabricated_tail():
    """Abstain-rồi-bịa (zero-hallucination): mọi đuôi sau câu abstain bị cắt fail-closed."""
    from app.agent.loop import _ABSTAIN_CANON, _clip_abstain

    fabricated = ("Không tìm thấy thông tin trong tài liệu nội bộ. Để nhập chứng từ, bạn cần: "
                  "1. Vào menu Mua hàng... 2. Nhập số phiếu...")
    assert _clip_abstain(fabricated) == _ABSTAIN_CANON        # đuôi bịa bị cắt
    assert "menu Mua hàng" not in _clip_abstain(fabricated)
    ok = "Bạn tạo phiếu nhập mua theo các bước [1]..."
    assert _clip_abstain(ok) == ok                            # câu trả lời thật giữ nguyên


@pytest.mark.asyncio
async def test_abstain_with_fabricated_steps_is_clipped_in_loop(monkeypatch, patch_retrieve):
    _mock_llm(monkeypatch, [
        json.dumps({"action": "answer", "answer":
                    "Không tìm thấy thông tin trong tài liệu nội bộ. Bạn hãy vào menu 'Mua hàng' "
                    "và chọn 'Nhập chứng từ mua hàng', sau đó nhập số phiếu 0000096..."}),
    ])
    sess = AgentSession(_FakeDB(), _identity(admin=True))
    out = await sess.step("huong dan nhap chung tu ...")
    assert out["grounded"] is False
    assert out["citations"] == []
    assert "Mua hàng" not in out["answer"]      # bước bịa KHÔNG được ship
    assert "0000096" not in out["answer"]


@pytest.mark.asyncio
async def test_long_exercise_query_is_condensed_before_retrieve(monkeypatch):
    """Câu đề-bài dài (>180 ký tự / nhiều dòng) phải được cô đọng thành truy vấn nghiệp vụ
    TRƯỚC khi retrieve — embedding câu thô bị số liệu/tên hàng kéo lệch chủ đề."""
    seen = {}

    async def fake_retrieve(db, identity, query, top_n=6, **kw):
        seen["query"] = query
        return []
    monkeypatch.setattr(agent_loop.retriever, "retrieve", fake_retrieve)

    calls = {"i": 0}

    async def fake_chat(messages, **kw):
        from app.llm.router import RoutingDecision
        calls["i"] += 1
        if calls["i"] == 1:      # lời gọi 1 = rephrase/cô đọng
            return "cách nhập phiếu nhập mua công nợ nhà cung cấp", RoutingDecision("local", "q", "t")
        return json.dumps({"action": "answer",
                           "answer": "Không tìm thấy thông tin trong tài liệu nội bộ."}), \
            RoutingDecision("local", "q", "t")
    monkeypatch.setattr(agent_loop.llm, "chat", fake_chat)

    long_q = ("huong dan nhap chung tu: \"7. Nhập mua NVL chưa thanh toán cho Công ty ABC theo "
              "phiếu nhập số 0000096, seri AP/14L, ngày 03/01, hạn thanh toán 30 ngày.\n"
              "20,000 nhựa trắng đơn giá 150\n40,000 nhựa xanh đơn giá 100\"")
    sess = AgentSession(_FakeDB(), _identity(admin=True))
    await sess.step(long_q)
    assert seen["query"] == "cách nhập phiếu nhập mua công nợ nhà cung cấp"  # đã cô đọng
