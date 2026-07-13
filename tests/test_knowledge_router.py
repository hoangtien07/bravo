from __future__ import annotations

from app.rag.knowledge_router import route_query


def test_end_user_question_scopes_to_end_user_playbook_before_retrieval():
    route = route_query("Hướng dẫn lên báo cáo tình hình tài chính")

    assert route.reason == "playbook"
    assert route.playbook_modes == ("end_user_guidance",)
    assert route.filters.source_types == ("user_guide", "mindmap", "basic_rule")
    assert "technical_manual" not in route.filters.source_types
    assert "kqpt_ptnv" not in route.filters.source_types


def test_technical_question_keeps_technical_scope():
    route = route_query("B30BizDoc lưu loại tài liệu nào?")

    assert "technical_manual" in route.filters.source_types
    assert "platform" in route.filters.modules


def test_unknown_question_remains_unscoped_instead_of_forcing_a_false_zero_hit():
    route = route_query("BRAVO có thể hỗ trợ gì cho tôi?")

    assert route.reason == "unscoped"
    assert not route.filters.active
