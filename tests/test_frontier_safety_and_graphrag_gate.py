import uuid

import pytest

from app.agent.computer_use import ComputerUsePolicyError, ComputerUseProposal, authorize_proposal
from app.config import Settings
from app.eval.graphrag_gate import GraphRAGMetrics, evaluate_gate
from app.security.rls import Identity


def _identity(*permissions: str) -> Identity:
    return Identity(employee_id=uuid.uuid4(), permissions=frozenset(permissions))


def test_computer_use_is_disabled_by_default():
    with pytest.raises(ComputerUsePolicyError):
        authorize_proposal(ComputerUseProposal("navigate", "https://erp.example.vn", "Xem trạng thái"),
                           _identity("computer:use"), Settings())


def test_computer_use_requires_https_allowlist_and_permission():
    settings = Settings(computer_use_enabled=True, computer_use_allowed_domains="erp.example.vn")
    proposal = ComputerUseProposal("click", "https://erp.example.vn/invoices", "Mở chi tiết", 1)
    with pytest.raises(ComputerUsePolicyError):
        authorize_proposal(proposal, _identity(), settings)
    authorize_proposal(proposal, _identity("computer:use"), settings)
    assert proposal.requires_approval is True


def test_graphrag_promotion_needs_relation_lift_without_regression():
    base = GraphRAGMetrics(.80, .60, 50, 100)
    pass_result = evaluate_gate(base, GraphRAGMetrics(.80, .66, 50, 140), {
        "min_relation_lift": .05, "max_overall_regression": .01,
        "min_relation_cases": 30, "max_p95_latency_multiplier": 1.5,
    })
    fail_result = evaluate_gate(base, GraphRAGMetrics(.77, .66, 50, 140), {
        "min_relation_lift": .05, "max_overall_regression": .01,
        "min_relation_cases": 30, "max_p95_latency_multiplier": 1.5,
    })
    assert pass_result.promote is True
    assert fail_result.promote is False
