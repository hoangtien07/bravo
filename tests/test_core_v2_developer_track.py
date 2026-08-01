"""Developer-track integration contract: all three synthetic V2 capabilities stay bounded."""
from decimal import Decimal

from app.api.routes_accounting_cases_v2 import router
from app.core_v2.demo_config import load_synthetic_demo_config
from app.core_v2.period_close_engine import ClosePrerequisite, assess_period_close
from app.core_v2.voucher_engine import VoucherEvidence, review_voucher


def test_developer_track_exposes_only_bounded_v2_routes_and_synthetic_config():
    paths = {route.path for route in router.routes}
    assert "/v2/accounting-cases/preview/voucher-review" in paths
    assert "/v2/accounting-cases/preview/period-close-readiness" in paths
    assert "/v2/accounting-cases/{case_id}/conversation" in paths
    assert load_synthetic_demo_config("file_system/core_v2_synthetic_demo.yaml").synthetic_only


def test_secondary_cases_fail_closed_and_never_produce_erp_execution():
    voucher = review_voucher(VoucherEvidence(Decimal("110"), Decimal("10"), Decimal("100"), None, None, None))
    close = assess_period_close((ClosePrerequisite("bank", True, "pending", True),), ())
    assert any(item.status == "abstain" for item in voucher)
    assert close.ready is False
    assert "did not execute" in close.execution
