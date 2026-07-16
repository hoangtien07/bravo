from app.api.routes_conversations import ChatIn


def test_chat_contract_accepts_consultant_ab_override():
    assert ChatIn(question="x", consultant_mode="off").consultant_mode == "off"
    assert ChatIn(question="x", consultant_mode="on").consultant_mode == "on"
    assert ChatIn(question="x", consultant_profile="implementation").consultant_profile == "implementation"
