from pathlib import Path

import pytest

from app.core_v2.demo_config import DemoConfigError, load_synthetic_demo_config
from app.config import Settings


_CONFIG = Path("file_system/core_v2_synthetic_demo.yaml")


def test_synthetic_demo_config_is_complete_and_denies_model_egress_until_pinned():
    config = load_synthetic_demo_config(_CONFIG)
    assert config.synthetic_only is True
    assert config.model_egress_policy == "deny_until_owner_pins_model"
    assert config.capability_flags["accounting_case_v2"] is True
    assert {item.value for item in config.functional_case_types} == {"bank_reconciliation", "voucher_evidence_review", "period_close_readiness"}
    assert not config.developer_preview_case_types


def test_demo_config_rejects_non_synthetic_mode(tmp_path):
    bad = tmp_path / "demo.yaml"
    bad.write_text(_CONFIG.read_text(encoding="utf-8").replace("synthetic_only: true", "synthetic_only: false"), encoding="utf-8")
    with pytest.raises(DemoConfigError):
        load_synthetic_demo_config(bad)


def test_v2_route_cannot_boot_without_a_synthetic_demo_manifest():
    with pytest.raises(RuntimeError, match="ACCOUNTING_CASE_V2_DEMO_CONFIG"):
        Settings(env="local", accounting_case_v2_enabled=True).validate_boot()


def test_v2_route_boots_with_the_versioned_synthetic_demo_manifest():
    Settings(
        env="local",
        accounting_case_v2_enabled=True,
        accounting_case_v2_demo_config=str(_CONFIG),
    ).validate_boot()


def test_v2_route_rejects_a_manifest_that_disables_its_capability(tmp_path):
    disabled = tmp_path / "disabled.yaml"
    disabled.write_text(
        _CONFIG.read_text(encoding="utf-8").replace("accounting_case_v2: true", "accounting_case_v2: false"),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="disabled by its synthetic demo manifest"):
        Settings(
            env="local",
            accounting_case_v2_enabled=True,
            accounting_case_v2_demo_config=str(disabled),
        ).validate_boot()
