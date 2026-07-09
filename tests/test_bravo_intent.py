from __future__ import annotations

from types import SimpleNamespace

from app.rag.bravo_intent import boost_for_bravo_intent, infer_query_intent


def _r(score: float, source_type: str, module: str, lifecycle_stage: str | None = None):
    extra = {"source_type": source_type, "module": module}
    if lifecycle_stage:
        extra["lifecycle_stage"] = lifecycle_stage
    return SimpleNamespace(score=score, extra=extra)


def test_infer_schema_question_prefers_technical_manual():
    intent = infer_query_intent("Bảng B30BizDoc dùng lưu loại tài liệu nào?")

    assert "technical_manual" in intent.source_types
    assert "platform" in intent.modules
    assert intent.lifecycle_stage == "technical_design"


def test_infer_framework_question_prefers_technical_context():
    intent = infer_query_intent(
        "Datasource Evaluator CommandValidators trong Editor khac nhau the nao?"
    )

    assert "technical_manual" in intent.source_types
    assert "platform" in intent.modules
    assert intent.lifecycle_stage == "technical_design"


def test_infer_testcase_question_prefers_kqpt_and_purchase():
    intent = infer_query_intent("Sinh testcase cho quy trình mua hàng có QC đầu vào")

    assert "kqpt_ptnv" in intent.source_types
    assert "purchase" in intent.modules
    assert "qc" in intent.modules


def test_boost_lifts_correct_source_type_over_close_score():
    wrong = _r(0.061, "user_guide", "purchase")
    right = _r(0.020, "technical_manual", "platform", "technical_design")

    ranked = boost_for_bravo_intent("B30AccDocPurchase lưu ở bảng nào?", [wrong, right])

    assert ranked[0] is right
    assert ranked[0].score > ranked[1].score


def test_boost_keeps_unknown_query_order():
    first = _r(0.2, "user_guide", "purchase")
    second = _r(0.1, "technical_manual", "platform")

    ranked = boost_for_bravo_intent("xin chao", [first, second])

    assert ranked == [first, second]
