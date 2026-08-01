from app.core_v2.bank_reasoning import SyntheticBankReasoning


def test_reasoning_explains_only_existing_finding_without_mutating_case():
    view = {"evidence": [{"snapshot_id": "e-bank"}], "findings": [{
        "finding_id": "finding-001", "finding_type": "BANK_ONLY", "severity": "high",
        "evidence_snapshot_ids": ["e-bank"], "check_result_ids": ["bank-check-001"],
    }]}
    reply = SyntheticBankReasoning().respond(view, "Giải thích finding-001")
    assert reply.kind == "explanation"
    assert reply.finding_ids == ("finding-001",)
    assert reply.rule_ids == ("bank-check-001",)
    assert reply.mutates_case is False


def test_reasoning_abstains_when_no_checked_finding_is_named():
    reply = SyntheticBankReasoning().respond({"evidence": [], "findings": []}, "Số dư hôm nay bao nhiêu?")
    assert reply.kind == "abstention"
    assert reply.mutates_case is False
