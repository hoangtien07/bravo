from __future__ import annotations

from app.agent.loop import AgentSession, _ABSTAIN_CANON
from app.agent.turn_contract import TurnContract, classify_turn, render_turn_contract


def test_db_creation_request_is_a_work_product_turn():
    contract = classify_turn(
        "Xác định rõ bài toán. Giờ cần tạo DB, hãy tạo giúp tôi",
        [{"kind": "image", "filename": "task.png"}],
    )
    assert contract.mode == "work_product"
    prompt = render_turn_contract(contract)
    assert "không phải chỉ là tra cứu tài liệu" in prompt
    assert "DDL/SQL/XML/code" in prompt
    assert "KHÔNG được trả câu abstain chung" in prompt


def test_regular_howto_question_keeps_knowledge_qa_contract():
    contract = classify_turn("Hướng dẫn lên báo cáo tình hình tài chính")
    assert contract.mode == "knowledge_qa"


def test_work_product_never_collapses_to_legacy_generic_abstain():
    session = AgentSession.__new__(AgentSession)
    session._turn_contract = TurnContract(mode="work_product", has_attachments=True)
    answer = session._normalize_answer(_ABSTAIN_CANON)
    assert not answer.startswith("Không tìm thấy thông tin trong tài liệu nội bộ")
    assert "DDL bảng và view tương tự" in answer


def test_knowledge_qa_retains_fail_closed_abstain():
    session = AgentSession.__new__(AgentSession)
    session._turn_contract = TurnContract(mode="knowledge_qa", has_attachments=False)
    assert session._normalize_answer(_ABSTAIN_CANON) == _ABSTAIN_CANON
