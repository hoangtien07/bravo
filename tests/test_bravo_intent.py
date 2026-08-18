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


def test_infer_cash_payment_with_bang_does_not_become_technical_design():
    """Accent folding must not turn ``bằng tiền mặt`` into a database-table request."""
    intent = infer_query_intent("Thanh toán công nợ bằng tiền mặt")

    assert intent.lifecycle_stage != "technical_design"
    assert "technical_manual" not in intent.source_types
    assert "platform" not in intent.modules


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


def test_infer_customization_integration_prefers_technical_manual():
    """Câu dev (tùy biến / tích hợp API / loại giao dịch) phải ưu tiên technical_manual —
    trước đây thiếu keyword nên kéo nhầm user_guide (T4/T7/T11 abstain)."""
    for q in (
        "quy trình tùy biến chức năng nghiệp vụ mà vẫn nâng cấp được",
        "cách tích hợp nhập xuất dữ liệu với hệ thống ngoài qua API",
        "tạo loại giao dịch mới với định khoản tự động",
        "khai báo Layout để thêm cột vào lưới dữ liệu",
    ):
        intent = infer_query_intent(q)
        assert "technical_manual" in intent.source_types, q


def test_boost_lifts_technical_manual_for_customization_query():
    results = [
        _r(0.30, "user_guide", "hrm"),
        _r(0.28, "technical_manual", "platform", "technical_design"),
    ]
    ordered = boost_for_bravo_intent("quy trình tùy biến chức năng trong BRAVO", results)
    assert ordered[0].extra["source_type"] == "technical_manual"  # kỹ thuật lên đầu
