from app.core_v2.period_close_engine import ClosePrerequisite, ReconciliationReference, assess_period_close


def test_required_stale_evidence_and_material_reconciliation_block_readiness():
    result = assess_period_close((ClosePrerequisite("bank-recon", True, "complete", False),),
                                 (ReconciliationReference("case_12345678", "unresolved", True),))
    assert result.ready is False
    assert result.blocker_ids == ("bank-recon", "case_12345678")
    assert "BRAVO did not execute close" in result.execution


def test_not_applicable_and_nonmaterial_unresolved_items_do_not_make_unsupported_blocker():
    result = assess_period_close((ClosePrerequisite("fx", False, "not_applicable", False),),
                                 (ReconciliationReference("case_12345678", "unresolved", False),))
    assert result.ready is True
    assert not result.blocker_ids
